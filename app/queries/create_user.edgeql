with
    name := <str>$name,
    NEW_USER := (
      insert default::User {
        name := name,
      }
    ),
select NEW_USER { * };