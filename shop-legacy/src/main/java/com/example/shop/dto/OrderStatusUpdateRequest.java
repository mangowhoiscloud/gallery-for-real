package com.example.shop.dto;

import javax.validation.constraints.NotNull;

public class OrderStatusUpdateRequest {

    @NotNull
    private String status;

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
}
