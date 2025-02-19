CREATE MIGRATION m1raar3baa5ifxal24gtcx6lorqjt4yoqmcn2fgpt4jhcncemaaana
    ONTO m1o3ndea7tn66zp53ibh562cilqrtv5e6gveav3n3hb43ja5bibyla
{
  ALTER TYPE default::Event {
      CREATE ACCESS POLICY anyone_can_create
          ALLOW INSERT ;
      ALTER LINK host {
          SET REQUIRED USING (SELECT
              default::User 
          LIMIT
              1
          );
      };
      CREATE ACCESS POLICY host_has_full_access
          ALLOW ALL USING ((.host ?= GLOBAL default::current_user));
  };
  ALTER TYPE default::User {
      CREATE ACCESS POLICY anyone_can_create
          ALLOW INSERT ;
      CREATE ACCESS POLICY self_has_full_access
          ALLOW ALL USING ((__subject__ ?= GLOBAL default::current_user));
      CREATE MULTI LINK events := (.<host[IS default::Event]);
  };
};
