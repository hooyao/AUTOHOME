package com.hy.autohome.config;

import com.hy.autohome.rest.DNSResource;
import org.glassfish.jersey.server.ResourceConfig;
import org.springframework.stereotype.Component;

@Component
public class JerseyConfig extends ResourceConfig {
    public JerseyConfig() {
        register(DNSResource.class);
    }
}
