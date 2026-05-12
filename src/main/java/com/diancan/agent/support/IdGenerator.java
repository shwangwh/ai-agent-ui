package com.diancan.agent.support;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Locale;
import java.util.concurrent.atomic.AtomicInteger;

public final class IdGenerator {
    private static final DateTimeFormatter FORMATTER = DateTimeFormatter.ofPattern("yyyyMMddHHmmss", Locale.ROOT);
    private static final AtomicInteger SEQUENCE = new AtomicInteger(1000);

    private IdGenerator() {
    }

    public static String next(String prefix) {
        return prefix + "_" + LocalDateTime.now().format(FORMATTER) + "_" + SEQUENCE.incrementAndGet();
    }
}
