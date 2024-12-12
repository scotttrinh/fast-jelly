with
    name := <str>$name,
    identity_id := <optional uuid>$identity_id,
    IDENTITY := (select ext::auth::Identity filter .id = identity_id),
    NEW_USER := (
      insert default::User {
        name := name,
        identities := IDENTITY
      }
    ),
select NEW_USER { * };