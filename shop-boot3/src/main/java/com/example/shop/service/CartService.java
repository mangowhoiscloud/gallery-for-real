package com.example.shop.service;

import com.example.shop.dto.CartItemAddRequest;
import com.example.shop.dto.CartItemResponse;
import com.example.shop.dto.CartItemUpdateRequest;
import com.example.shop.dto.CartResponse;
import com.example.shop.entity.Cart;
import com.example.shop.entity.CartItem;
import com.example.shop.entity.Member;
import com.example.shop.entity.Product;
import com.example.shop.entity.ProductStatus;
import com.example.shop.mapper.CartItemMapper;
import com.example.shop.mapper.CartMapper;
import com.example.shop.mapper.MemberMapper;
import com.example.shop.mapper.ProductMapper;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.List;
import java.util.NoSuchElementException;

@Service
@Transactional
public class CartService {

    private final CartMapper cartMapper;
    private final CartItemMapper cartItemMapper;
    private final ProductMapper productMapper;
    private final MemberMapper memberMapper;

    public CartService(CartMapper cartMapper, CartItemMapper cartItemMapper,
                       ProductMapper productMapper, MemberMapper memberMapper) {
        this.cartMapper = cartMapper;
        this.cartItemMapper = cartItemMapper;
        this.productMapper = productMapper;
        this.memberMapper = memberMapper;
    }

    public CartResponse getCart(String email) {
        Member member = requireMember(email);
        Cart cart = getOrCreateCart(member.getId());
        return buildCartResponse(cart);
    }

    public CartResponse addItem(String email, CartItemAddRequest request) {
        Member member = requireMember(email);

        Product product = productMapper.findById(request.productId());
        if (product == null) {
            throw new NoSuchElementException("Product not found: " + request.productId());
        }
        if (product.getStatus() != ProductStatus.ACTIVE) {
            throw new IllegalArgumentException("Product is not available: " + request.productId());
        }

        Cart cart = getOrCreateCart(member.getId());

        CartItem existing = cartItemMapper.findItemByCartIdAndProductId(cart.getId(), request.productId());
        if (existing != null) {
            int newQty = existing.getQuantity() + request.quantity();
            if (newQty > product.getStockQuantity()) {
                throw new IllegalArgumentException("Insufficient stock. Available: " + product.getStockQuantity());
            }
            cartItemMapper.updateItemQuantity(existing.getId(), newQty);
        } else {
            if (request.quantity() > product.getStockQuantity()) {
                throw new IllegalArgumentException("Insufficient stock. Available: " + product.getStockQuantity());
            }
            CartItem item = new CartItem();
            item.setCartId(cart.getId());
            item.setProductId(request.productId());
            item.setQuantity(request.quantity());
            cartItemMapper.insertItem(item);
        }

        return buildCartResponse(cart);
    }

    public CartResponse updateItem(String email, Long itemId, CartItemUpdateRequest request) {
        Member member = requireMember(email);
        Cart cart = cartMapper.findByMemberId(member.getId());
        if (cart == null) {
            throw new NoSuchElementException("Cart item not found: " + itemId);
        }

        CartItem entity = cartItemMapper.findEntityById(itemId);
        if (entity == null || !entity.getCartId().equals(cart.getId())) {
            throw new NoSuchElementException("Cart item not found: " + itemId);
        }

        Product product = productMapper.findById(entity.getProductId());
        if (product != null && request.quantity() > product.getStockQuantity()) {
            throw new IllegalArgumentException("Insufficient stock. Available: " + product.getStockQuantity());
        }

        cartItemMapper.updateItemQuantity(itemId, request.quantity());
        return buildCartResponse(cart);
    }

    public void removeItem(String email, Long itemId) {
        Member member = requireMember(email);
        Cart cart = cartMapper.findByMemberId(member.getId());
        if (cart == null) {
            throw new NoSuchElementException("Cart item not found: " + itemId);
        }

        CartItem entity = cartItemMapper.findEntityById(itemId);
        if (entity == null || !entity.getCartId().equals(cart.getId())) {
            throw new NoSuchElementException("Cart item not found: " + itemId);
        }

        cartItemMapper.deleteItem(itemId);
    }

    public void clearCart(String email) {
        Member member = requireMember(email);
        Cart cart = cartMapper.findByMemberId(member.getId());
        if (cart != null) {
            cartItemMapper.deleteAllItems(cart.getId());
        }
    }

    private Member requireMember(String email) {
        Member member = memberMapper.findByEmail(email);
        if (member == null) {
            throw new NoSuchElementException("Member not found: " + email);
        }
        return member;
    }

    private Cart getOrCreateCart(Long memberId) {
        Cart cart = cartMapper.findByMemberId(memberId);
        if (cart == null) {
            cart = new Cart();
            cart.setMemberId(memberId);
            cartMapper.insertCart(cart);
        }
        return cart;
    }

    private CartResponse buildCartResponse(Cart cart) {
        List<CartItemResponse> items = cartItemMapper.findCartItems(cart.getId());
        BigDecimal cartTotal = items.stream()
                .map(CartItemResponse::subtotal)
                .reduce(BigDecimal.ZERO, BigDecimal::add);
        return new CartResponse(cart.getId(), items, cartTotal);
    }
}
