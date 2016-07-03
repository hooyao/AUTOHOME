package com.hy.autohome.config;

import org.flywaydb.core.Flyway;
import org.flywaydb.core.internal.util.jdbc.JdbcUtils;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.autoconfigure.jdbc.DataSourceBuilder;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.ApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.SQLException;

@Configuration
@EnableAutoConfiguration
public class DatabaseConfig {

    @Bean
    @ConfigurationProperties(prefix="spring.datasource")
    public DataSource primaryDataSource() {
        return DataSourceBuilder.create().build();
    }

    @Bean
    public Flyway flywayMigBean(DataSource dataSource, ApplicationContext applicationContext){
        Flyway flyway = new Flyway();
        flyway.setDataSource(dataSource);
        flyway.setBaselineOnMigrate(true);
        flyway.setTable("schema_version");
        flyway.setLocations("classpath:db");
        //setDbTransactionControl("LOCKS",dataSource);
        createSchema(dataSource);
        flyway.migrate();
        //setDbTransactionControl("MVCC",dataSource);
        return flyway;
    }

    private void createSchema(DataSource ds) {
        Connection connection = null;
        try {
            connection = JdbcUtils.openConnection(ds);
            //connection.createStatement().execute("SET DATABASE TRANSACTION CONTROL " + mode);
            connection.createStatement().execute("CREATE SCHEMA HUYAO");
        } catch (SQLException e) {
            //log it
            JdbcUtils.closeConnection(connection);
        } finally {
            JdbcUtils.closeConnection(connection);
        }
    }

}
