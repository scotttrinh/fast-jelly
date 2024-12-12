CREATE MIGRATION m1fhbkkl7nsssusryzirvd65engpgt32iini6pz3vrjztoxksbleta
    ONTO initial
{
  CREATE ABSTRACT TYPE default::Auditable {
      CREATE REQUIRED PROPERTY created_at: std::datetime {
          SET default := (std::datetime_of_statement());
          SET readonly := true;
      };
  };
  CREATE SCALAR TYPE default::str50 EXTENDING std::str {
      CREATE CONSTRAINT std::max_len_value(50);
  };
  CREATE TYPE default::User EXTENDING default::Auditable {
      CREATE REQUIRED PROPERTY name: default::str50 {
          CREATE CONSTRAINT std::exclusive;
      };
  };
  CREATE TYPE default::Event EXTENDING default::Auditable {
      CREATE LINK host: default::User;
      CREATE PROPERTY address: std::str;
      CREATE REQUIRED PROPERTY name: default::str50 {
          CREATE CONSTRAINT std::exclusive;
      };
      CREATE PROPERTY schedule: std::datetime;
  };
};
