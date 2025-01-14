import asyncio
import os
import secrets

from edgedb import create_async_client

async def main():
    client = create_async_client()

    auth_signing_key = os.getenv("GEL_AUTH_SIGNING_KEY", secrets.token_urlsafe(32))

    await client.execute(
        f"""
configure current branch reset ext::auth::AuthConfig;
configure current branch reset ext::auth::ProviderConfig;
configure current branch reset ext::auth::EmailPasswordProviderConfig;
configure current branch reset cfg::EmailProviderConfig;

configure current branch set
ext::auth::AuthConfig::auth_signing_key := "{auth_signing_key}";

configure current branch set
ext::auth::AuthConfig::app_name := "Fast Jelly";

configure current branch set
ext::auth::AuthConfig::allowed_redirect_urls := {{"http://localhost:8000"}};

configure current branch insert
ext::auth::EmailPasswordProviderConfig {{
    require_verification := true,
}};

configure current branch insert
cfg::SMTPProviderConfig {{
    name := "mailpit",
    host := "localhost",
    port := 1025,
    username := "smtpuser",
    password := "smtppassword",
    sender := "no-reply@example.com",
    validate_certs := false,
}};

configure current branch set
cfg::current_email_provider_name := "mailpit";
        """
    )

if __name__ == "__main__":
    asyncio.run(main())
  