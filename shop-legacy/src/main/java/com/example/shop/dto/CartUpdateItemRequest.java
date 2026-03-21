package com.example.shop.dto;

import javax.validation.constraints.Min;
import javax.validation.constraints.NotNull;

public class CartUpdateItemRequest {

    @NotNull
    @Min(1)
    private Integer quantity;

    public Integer getQuantity() { return quantity; }
    public void setQuantity(Integer quantity) { this.quantity = quantity; }
}
