package com.hy.autohome;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.ComponentScan;

@SpringBootApplication
@ComponentScan("com.hy.autohome.*")
public class AutohomeApplication {

	public static void main(String[] args) {
		SpringApplication.run(AutohomeApplication.class, args);
	}
}
