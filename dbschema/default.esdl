using extension auth;

module default {
    single global current_user := assert_single((
        select User
        filter global ext::auth::ClientTokenIdentity in .identities
    ));

    abstract type Auditable {
        required created_at: datetime {
            readonly := true;
            default := datetime_of_statement();
        };
    }

    scalar type str50 extending str {
        constraint max_len_value(50);
    }

    type User extending Auditable {
        required name: str50 {
            constraint exclusive;
        };
        multi identities: ext::auth::Identity {
            constraint exclusive;
        };
    }

    type Event extending Auditable {
        required name: str50 {
            constraint exclusive;
        };
        address: str;
        schedule: datetime;
        host: User;
    }
}
