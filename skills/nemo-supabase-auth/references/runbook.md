# Supabase Google Auth Runbook

This runbook is operational guidance for `$nemo-supabase-auth`. It does not grant mutation authority.

## 1. Lock scope and identities

Resolve these values through read-only inspection:

- absolute application root, source revision, dirty files, framework, auth SDK version, SSR/client split;
- production, preview, and local origins;
- login entrypoint, application callback route, default safe destination, protected route or API;
- exact Supabase organization/project/environment and project ref;
- exact Google account/organization and matching Google Cloud projects/OAuth Web clients;
- current Google audience, publication state, requested scopes, and test-user state as redacted enums/counts;
- current Supabase Google provider enable state, Site URL, and Redirect URLs.

Do not use a project name alone as identity evidence. Combine provider account/organization, immutable provider target where available, and live project readback. If two resources could both be the intended target, stop before mutation.

## 2. Inspect the application before provider work

Search existing project patterns before adding code:

- `signInWithOAuth`, `provider: 'google'`, and `redirectTo`;
- callback routes and `exchangeCodeForSession`;
- existing Supabase browser/server clients and cookie adapters;
- middleware or server-side protected-route checks;
- URL/environment utilities already used by the project;
- auth tests and error pages.

Reuse the current abstraction. Do not add a second Supabase client factory or a new auth framework when the project already has one.

For an SSR/PKCE callback, the minimum behavior is:

1. parse `code` and an optional `next` from the incoming URL without logging the raw query;
2. validate `next` as a safe internal path;
3. call `exchangeCodeForSession(code)` once with the existing server client;
4. redirect to the safe destination on success;
5. redirect to a stable, non-sensitive error page on failure;
6. prove identity on the server with the current official trusted-user or claims method.

Reject `next` when it is empty but not intentionally defaulted, begins with `//`, contains a backslash, parses as an absolute URL, or becomes external after one decode. A fixed internal default is safer than trying to repair invalid input.

## 3. Build the exact URL matrix

Use static configuration URLs only. Never record the runtime callback URL containing an authorization code.

Example for a hosted Supabase project:

| Key | Example |
|---|---|
| Supabase Auth origin used by current Google setup guidance | `https://project-ref.supabase.co` |
| Google redirect URI | `https://project-ref.supabase.co/auth/v1/callback` |
| Supabase Site URL | `https://app.example.com` |
| Supabase production redirect | `https://app.example.com/auth/callback` |
| Application `redirectTo` | `https://app.example.com/auth/callback` |
| Local application redirect | `http://localhost:3000/auth/callback` |

Rules:

- Google Authorized JavaScript origins are origins only. No path, query, or fragment.
- Google Authorized redirect URI is the Supabase provider callback, not the application route.
- Supabase Redirect URLs contain application destinations accepted from `redirectTo`.
- Production uses exact URLs. If preview deployments require a wildcard, document why and choose the narrowest currently supported pattern.
- Compare scheme, hostname, port, path, case-sensitive segments, and trailing slash exactly.

## 4. Decide reuse versus creation

For every existing Google Web client, compare only non-secret configuration:

- owning account/organization and Google Cloud project;
- client type;
- application purpose/name;
- Authorized JavaScript origins;
- Authorized redirect URIs;
- audience/publication state compatibility.

Reuse when one client is clearly owned by this application and the required minimum edit is safe. Create a new client when no compatible resource exists or the user explicitly requested isolation. Do not repurpose a client used by an unrelated production application.

Creating a Google Cloud project is a persistent external mutation. Record the exact intended display name and generated/selected project identity through provider readback. Do not attach billing or enable unrelated APIs.

## 5. Configure Google Auth Platform

Provider labels can change; follow the current live flow instead of fixed screen coordinates.

1. Select the exact Google Cloud project and read it back.
2. Configure branding only with user-approved public product data.
3. Select Workspace internal or external based on the actual audience; do not infer this from repository visibility.
4. Keep an external app in Testing unless Production publication is explicitly authorized and requirements are understood.
5. Use only `openid`, email, and profile for ordinary Supabase Google login. Any additional scope needs a stated product requirement and separate authorization.
6. Let the user select personal test accounts directly in the provider UI. Record only a redacted state such as `configured`, never an address.
7. Create or update one Web application client with the URL matrix values.
8. Read the non-secret origins/redirects back before moving to Supabase.

## 6. Transfer the Google client into Supabase

The agent may identify and verify the client ID. The Client secret follows a human-in-the-loop handoff:

1. Confirm the browser is on the exact Google client and exact Supabase project.
2. Ask the user to copy the secret directly from Google into the Supabase provider field without pasting it into chat, terminal, notes, or a report.
3. Do not inspect clipboard history or browser storage.
4. After the user confirms completion, read back only `configured` / `present` state if the provider exposes it; never reveal the value.
5. Enable Google provider and save.

If the value is ever exposed in tool output, stop the workflow and require rotation before continuing.

## 7. Configure Supabase URL settings

Treat this as a separate action from enabling the Google provider:

1. Snapshot current Site URL and Redirect URLs.
2. Set Site URL to the production application origin.
3. Add exact application callback URLs for authorized environments.
4. Remove an existing URL only when the user authorized removal and its consumers were checked.
5. Save and read back the entire non-secret allowlist.

For preview wildcards, verify the current Supabase syntax from official docs. Do not invent glob rules from memory.

## 8. Verify in layers

### Static and project-native checks

- run the existing formatter/linter/typecheck/tests relevant to the changed auth files;
- add focused tests for callback exchange, missing/invalid code, and safe `next` when the project test stack supports them;
- inspect the built or runtime environment mapping so production does not silently use localhost.

### Provider checks

- Google client type, exact origins, exact redirect URI, audience, publication state, and minimum scopes;
- Supabase Google provider enabled state, client-ID association, secret-present state, Site URL, and redirect allowlist.

### Real browser check

Before clicking sign-in, state the persistent effects: a Google grant may be recorded, a Supabase user may be created or reused, and a session will be created.

On an authorized run:

1. start from a clean signed-out application state without dumping storage;
2. initiate Google login from the application;
3. confirm the Google surface corresponds to the expected client/brand;
4. complete consent/account selection through user interaction when personal data is involved;
5. verify the browser returns through Supabase to the exact application callback;
6. verify a server-trusted authenticated boolean signal;
7. open one protected page/API and observe success;
8. sign out and verify the same protected resource now rejects or redirects.

Do not take screenshots containing account chooser details, email, avatar, callback query, DevTools storage, or network authorization headers.

## 9. Diagnose common failures

### `redirect_uri_mismatch`

- capture the expected URI from a sanitized provider error or current request construction without retaining query data;
- compare it character-for-character with Google client readback;
- verify the value is the Supabase provider callback, not the app callback;
- check that the request is using the intended Supabase project/environment.

### Provider disabled or unsupported provider

- read back the exact Supabase project;
- verify the Google provider is enabled and saved;
- do not assume the client secret is correct merely because a masked field exists.

### Callback reaches the app but no session exists

- verify the callback route exchanges the code exactly once;
- verify the project’s server client can write the expected auth cookie through its existing adapter;
- check host/scheme consistency and middleware redirects;
- report errors without raw URL queries or identity data.

### Login loop

- trace only redacted route names: app login → Google → Supabase callback → app callback → destination;
- compare Site URL, Redirect URLs, and `redirectTo`;
- check whether protected middleware runs before callback exchange;
- check relative `next` validation and the default destination.

### Works locally but not in production

- confirm production environment variables reference the intended Supabase project without printing values;
- compare exact production callback allowlist, HTTPS scheme, hostname, path, and trailing slash;
- confirm the deployed revision contains the verified callback code;
- run a production browser check only after provider readback matches.

## 10. Handoff states

- `audit_only`: no mutation performed; return current state, conflicts, URL matrix, and next exact action.
- `code_ready`: code checks pass; provider mutations remain pending.
- `configuration_ready`: code, URL matrix, Google, and Supabase readbacks pass; real login may still be missing.
- `end_to_end_verified`: authorized real login, callback, trusted-user, protected-route, and logout-negative checks pass with no missing evidence.
- `blocked`: identify the exact missing authority or evidence; do not widen scope.
