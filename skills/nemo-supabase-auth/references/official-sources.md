# Official Sources

Last reviewed: 2026-08-21.

## Supabase

1. [Login with Google](https://supabase.com/docs/guides/auth/social-login/auth-google)
   - Current guide inspected on 2026-08-21.
   - Grounded contract: create a Google Web application client, use the Supabase Auth/provider callback as Google’s authorized redirect URI, then configure the Google provider in the exact Supabase project.
   - The guide links into the current Google Auth Platform surfaces; those UI labels remain runtime facts.

2. [Redirect URLs](https://supabase.com/docs/guides/auth/redirect-urls)
   - Current guide inspected on 2026-08-21.
   - Grounded contract: Site URL is the default redirect target; `redirectTo` must match the configured redirect allowlist; production should use exact redirect paths, while wildcard patterns are mainly for local/preview needs.

3. [Supabase changelog](https://supabase.com/changelog)
   - Reviewed on 2026-08-21 for Auth behavior changes before authoring this package.
   - Recheck before each live mutation because Auth helpers, dashboard surfaces, and provider behavior can change.

## Google evidence boundary

Direct Google Developers/Auth Platform documentation pages timed out through the available retrieval paths on 2026-08-21. Therefore:

- direct-current Google-document inspection is `missing_evidence` for this package version;
- the Skill does not claim stable Google Console button names or screen sequence;
- live Google provider readback plus the current Supabase official guide is required before mutation;
- audience, publication, verification, and scope decisions that exceed basic `openid`, email, and profile remain separate user decisions.

Do not replace this boundary with blog posts, screenshots, or remembered UI labels. Refresh this file when direct Google official documentation can be inspected successfully.

## Mutable facts that always require refresh

- Google Auth Platform navigation, project quotas, audience/publication rules, brand verification, and credential UI;
- Supabase Dashboard navigation, Google provider fields, Site URL/Redirect URLs behavior, SSR/PKCE recommendations, and wildcard syntax;
- framework-specific Supabase client helpers and trusted server-side identity methods;
- any claim that a real provider configuration or browser login succeeded.
