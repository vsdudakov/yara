import typing as tp

from yara.apps.security import middlewares
from yara.core.apps import YaraApp
from yara.core.middlewares import YaraMiddleware
from yara.settings import YaraSettings


class SecurityApp(YaraApp):
    def get_middlewares(self) -> list[tuple[type[YaraMiddleware], dict[str, tp.Any]]]:
        settings: YaraSettings = self.root_app.settings
        return [
            (tp.cast(type[YaraMiddleware], middlewares.SentryAsgiMiddleware), {}),
            (
                tp.cast(type[YaraMiddleware], middlewares.RawContextMiddleware),
                {
                    "plugins": (
                        middlewares.plugins.ForwardedForPlugin(),
                        middlewares.plugins.RequestIdPlugin(),
                        middlewares.plugins.UserAgentPlugin(),
                        middlewares.RefererPlugin(),
                        middlewares.TokenPlugin(),
                        middlewares.HostIPPlugin(),
                    ),
                },
            ),
            (
                tp.cast(type[YaraMiddleware], middlewares.CORSMiddleware),
                {
                    "allow_origins": settings.CORS_ORIGINS,
                    "allow_credentials": True,
                    "allow_methods": ["*"],
                    "allow_headers": ["*"],
                },
            ),
            (
                tp.cast(type[YaraMiddleware], middlewares.SecureMiddleware),
                {
                    "secure_headers": middlewares.secure.Secure(
                        # Policies
                        hsts=(
                            middlewares.secure.StrictTransportSecurity()
                            .max_age(settings.SEC_HSTS_MAX_AGE)
                            .include_subdomains()
                            .preload()
                        ),
                        # Secure Headers
                        xfo=None,
                        csp=None,
                        xxp=middlewares.secure.XXSSProtection().set(settings.SEC_XSS_PROTECTION),
                        referrer=middlewares.secure.ReferrerPolicy().same_origin(),
                        content=middlewares.secure.XContentTypeOptions().set(settings.SEC_XCONTENT_TYPE),
                        cache=(
                            middlewares.secure.CacheControl()
                            .s_maxage(settings.SEC_CACHE_CONTROL_S_MAXAGE)
                            .no_cache()
                            .no_store()
                            .must_revalidate()
                            .private()
                        ),
                    ),
                },
            ),
            (
                tp.cast(type[YaraMiddleware], middlewares.SecureExtendedMiddleware),
                {
                    "header": "X-DNS-Prefetch-Control",
                    "value": settings.SEC_XDNS_PREFETCH_CONTROL,
                    "policies": settings.SEC_XDNS_PREFETCH_CONTROL_POLICIES,
                },
            ),
            (
                tp.cast(type[YaraMiddleware], middlewares.SecureExtendedMiddleware),
                {
                    "header": "X-Permitted-Cross-Domain-Policies",
                    "value": settings.SEC_XPERMITTED_CDP,
                    "policies": settings.SEC_XPERMITTED_CDP_POLICIES,
                },
            ),
            (
                tp.cast(type[YaraMiddleware], middlewares.SecureExtendedMiddleware),
                {
                    "header": "Cross-Origin-Opener-Policy",
                    "value": settings.SEC_CROSS_ORIGIN_OPENER,
                    "policies": settings.SEC_CROSS_ORIGIN_OPENER_POLICIES,
                },
            ),
            (
                tp.cast(type[YaraMiddleware], middlewares.SecureExtendedMiddleware),
                {
                    "header": "Cross-Origin-Resource-Policy",
                    "value": settings.SEC_CROSS_ORIGIN_RESOURCE,
                    "policies": settings.SEC_CROSS_ORIGIN_RESOURCE_POLICIES,
                },
            ),
            (
                tp.cast(type[YaraMiddleware], middlewares.SecureExtendedMiddleware),
                {
                    "header": "Expect-CT",
                    "value": "; ".join([f"max-age={settings.SEC_EXPECTCT_MAX_AGE}", "enforce"]),
                    "policies": settings.SEC_EXPECTCT_POLICIES,
                },
            ),
        ]
