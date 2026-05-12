package com.diancan.agent.controller;

import com.diancan.agent.dto.ApiError;
import com.diancan.agent.support.BadRequestException;
import com.diancan.agent.support.ResourceNotFoundException;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.time.OffsetDateTime;

@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(ResourceNotFoundException.class)
    @ResponseStatus(HttpStatus.NOT_FOUND)
    public ApiError notFound(ResourceNotFoundException ex) {
        return new ApiError("NOT_FOUND", ex.getMessage(), OffsetDateTime.now());
    }

    @ExceptionHandler({BadRequestException.class, MethodArgumentNotValidException.class, IllegalArgumentException.class})
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public ApiError badRequest(Exception ex) {
        return new ApiError("BAD_REQUEST", ex.getMessage(), OffsetDateTime.now());
    }
}
