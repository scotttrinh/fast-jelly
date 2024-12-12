with
    name := <str>$name,
    address := <str>$address,
    schedule := <datetime>$schedule,
    host_name := <str>$host_name,

    HOST := (select default::User filter .name = host_name),
    CREATED := (
        insert default::Event {
            name := name,
            address := address,
            schedule := schedule,
            host := HOST,
        }
    ),
select CREATED { *, host: { * } };
