with
    name := <str>$name,
select default::User { * }
filter .name = name;
