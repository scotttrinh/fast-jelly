with
    name := <optional str>$name,
    identity_id := <optional uuid>$identity_id,
    IDENTITY := (select ext::auth::Identity filter .id = identity_id),
    NEW_USER := (
      insert default::User {
        name := name ??
          assert_single(
            IDENTITY.<identity[is ext::auth::EmailFactor].email
          ) ??
          to_str(datetime_of_statement()),
        identities := IDENTITY
      }
    ),
select NEW_USER { * };