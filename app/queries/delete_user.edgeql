with
    name := <str>$name,
    DELETED := (
      delete default::User filter .name = name
    )
select DELETED { * };
