package com.example.shop.mapper;

import com.example.shop.dto.CartItemResponse;
import com.example.shop.entity.CartItem;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface CartItemMapper {

    void insertItem(CartItem item);

    List<CartItemResponse> findCartItems(Long cartId);

    CartItemResponse findItemById(Long itemId);

    void updateItemQuantity(@Param("itemId") Long itemId, @Param("quantity") int quantity);

    void deleteItem(Long itemId);

    void deleteAllItems(Long cartId);

    CartItem findEntityById(Long itemId);

    CartItem findItemByCartIdAndProductId(@Param("cartId") Long cartId, @Param("productId") Long productId);
}
