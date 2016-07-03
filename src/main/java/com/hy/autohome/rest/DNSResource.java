package com.hy.autohome.rest;

import javax.ws.rs.GET;
import javax.ws.rs.Path;

@Path("dns")
public class DNSResource {

    @GET
    public String test(){
        return "hello world";
    }
}
