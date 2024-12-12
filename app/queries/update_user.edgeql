with
    current_name := <str>$current_name,
    new_name := <str>$new_name,
    USER := (select default::User filter .name = current_name),
    UPDATED := (
        update USER
        set {
            name := new_name,
        }
    ),
select UPDATED { * };
