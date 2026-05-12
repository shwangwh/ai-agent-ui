package com.diancan.agent.controller;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/config")
public class ConfigController {
    private final List<Map<String, Object>> environments = new ArrayList<>();
    private final List<Map<String, Object>> accounts = new ArrayList<>();

    public ConfigController() {
        environments.add(Map.of("environmentCode", "test", "baseUrl", "http://localhost:3000", "domainWhitelist", List.of("localhost")));
    }

    @GetMapping("/environments")
    public List<Map<String, Object>> environments() {
        return environments;
    }

    @PostMapping("/environments")
    public Map<String, Object> createEnvironment(@RequestBody Map<String, Object> environment) {
        environments.add(environment);
        return environment;
    }

    @GetMapping("/accounts")
    public List<Map<String, Object>> accounts() {
        return accounts;
    }

    @PostMapping("/accounts")
    public Map<String, Object> createAccount(@RequestBody Map<String, Object> account) {
        Map<String, Object> masked = new java.util.HashMap<>(account);
        if (masked.containsKey("password")) {
            masked.put("password", "******");
        }
        accounts.add(masked);
        return masked;
    }
}
