CREATE MIGRATION m1o3ndea7tn66zp53ibh562cilqrtv5e6gveav3n3hb43ja5bibyla
    ONTO m1fhbkkl7nsssusryzirvd65engpgt32iini6pz3vrjztoxksbleta
{
  CREATE EXTENSION pgcrypto VERSION '1.3';
  CREATE EXTENSION auth VERSION '1.0';
  ALTER TYPE default::User {
      CREATE MULTI LINK identities: ext::auth::Identity {
          CREATE CONSTRAINT std::exclusive;
      };
  };
  CREATE SINGLE GLOBAL default::current_user := (std::assert_single((SELECT
      default::User
  FILTER
      (GLOBAL ext::auth::ClientTokenIdentity IN .identities)
  )));
};
