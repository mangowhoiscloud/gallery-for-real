package com.example.shop.mapper;

import com.example.shop.dto.CartItemResponse;
import com.example.shop.entity.*;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.List;

import static org.assertj.core.api.Assertions.*;

@SpringBootTest
@ActiveProfiles("test")
@Transactional
class CartItemMapperTest {

    @Autowired CartItemMapper cartItemMapper;
    @Autowired CartMapper     cartMapper;
    @Autowired MemberMapper   memberMapper;
    @Autowired ProductMapper  productMapper;

    private Cart cart;
    private Product product;

    @BeforeEach
    void setUp() {
        Member member = new Member();
        member.setEmail("cartitem-test@example.com");
        member.setPassword("hashed");
        member.setName("Item Tester");
        member.setPhone("01099998888");
        member.setAddress("Busan");
        member.setRole(MemberRole.USER);
        member.setActive(true);
        memberMapper.insert(member);

        cart = new Cart();
        cart.setMemberId(member.getId());
        cartMapper.insertCart(cart);

        product = new Product();
        product.setName("Test Product");
        product.setDescription("A product");
        product.setPrice(new BigDecimal("19.99"));
        product.setStockQuantity(100);
        product.setCategory("Electronics");
        product.setImageUrl("https://example.com/img/test.jpg");
        product.setStatus(ProductStatus.ACTIVE);
        productMapper.insert(product);
    }

    @Test
    void insertItem_andFindCartItems_withEnrichedFields() {
        CartItem item = new CartItem();
        item.setCartId(cart.getId());
        item.setProductId(product.getId());
        item.setQuantity(3);
        cartItemMapper.insertItem(item);

        assertThat(item.getId()).isNotNull();

        List<CartItemResponse> items = cartItemMapper.findCartItems(cart.getId());
        assertThat(items).hasSize(1);

        CartItemResponse resp = items.get(0);
        assertThat(resp.itemId()).isEqualTo(item.getId());
        assertThat(resp.productId()).isEqualTo(product.getId());
        assertThat(resp.productName()).isEqualTo("Test Product");
        assertThat(resp.productPrice()).isEqualByComparingTo(new BigDecimal("19.99"));
        assertThat(resp.imageUrl()).isEqualTo("https://example.com/img/test.jpg");
        assertThat(resp.quantity()).isEqualTo(3);
        assertThat(resp.subtotal()).isEqualByComparingTo(new BigDecimal("59.97"));
        assertThat(resp.productStatus()).isEqualTo("ACTIVE");
    }

    @Test
    void findItemById_returnsEnrichedItem() {
        CartItem item = new CartItem();
        item.setCartId(cart.getId());
        item.setProductId(product.getId());
        item.setQuantity(2);
        cartItemMapper.insertItem(item);

        CartItemResponse resp = cartItemMapper.findItemById(item.getId());
        assertThat(resp).isNotNull();
        assertThat(resp.itemId()).isEqualTo(item.getId());
        assertThat(resp.quantity()).isEqualTo(2);
        assertThat(resp.subtotal()).isEqualByComparingTo(new BigDecimal("39.98"));
    }

    @Test
    void updateItemQuantity_changesQuantityAndSubtotal() {
        CartItem item = new CartItem();
        item.setCartId(cart.getId());
        item.setProductId(product.getId());
        item.setQuantity(1);
        cartItemMapper.insertItem(item);

        cartItemMapper.updateItemQuantity(item.getId(), 5);

        CartItemResponse resp = cartItemMapper.findItemById(item.getId());
        assertThat(resp.quantity()).isEqualTo(5);
        assertThat(resp.subtotal()).isEqualByComparingTo(new BigDecimal("99.95"));
    }

    @Test
    void deleteItem_removesOnlyTargetItem() {
        CartItem item1 = new CartItem();
        item1.setCartId(cart.getId());
        item1.setProductId(product.getId());
        item1.setQuantity(1);
        cartItemMapper.insertItem(item1);

        Product product2 = new Product();
        product2.setName("Product Two");
        product2.setDescription("Another product");
        product2.setPrice(new BigDecimal("9.99"));
        product2.setStockQuantity(50);
        product2.setCategory("Books");
        product2.setImageUrl("https://example.com/img/two.jpg");
        product2.setStatus(ProductStatus.ACTIVE);
        productMapper.insert(product2);

        CartItem item2 = new CartItem();
        item2.setCartId(cart.getId());
        item2.setProductId(product2.getId());
        item2.setQuantity(2);
        cartItemMapper.insertItem(item2);

        cartItemMapper.deleteItem(item1.getId());

        List<CartItemResponse> items = cartItemMapper.findCartItems(cart.getId());
        assertThat(items).hasSize(1);
        assertThat(items.get(0).itemId()).isEqualTo(item2.getId());
    }

    @Test
    void deleteAllItems_clearsCart() {
        CartItem item1 = new CartItem();
        item1.setCartId(cart.getId());
        item1.setProductId(product.getId());
        item1.setQuantity(2);
        cartItemMapper.insertItem(item1);

        Product product2 = new Product();
        product2.setName("Another Product");
        product2.setDescription("Desc");
        product2.setPrice(new BigDecimal("5.00"));
        product2.setStockQuantity(20);
        product2.setCategory("Books");
        product2.setImageUrl("https://example.com/img/another.jpg");
        product2.setStatus(ProductStatus.ACTIVE);
        productMapper.insert(product2);

        CartItem item2 = new CartItem();
        item2.setCartId(cart.getId());
        item2.setProductId(product2.getId());
        item2.setQuantity(1);
        cartItemMapper.insertItem(item2);

        cartItemMapper.deleteAllItems(cart.getId());

        List<CartItemResponse> items = cartItemMapper.findCartItems(cart.getId());
        assertThat(items).isEmpty();
    }

    @Test
    void uniqueConstraint_preventsInsertingDuplicateProduct() {
        CartItem item1 = new CartItem();
        item1.setCartId(cart.getId());
        item1.setProductId(product.getId());
        item1.setQuantity(1);
        cartItemMapper.insertItem(item1);

        CartItem item2 = new CartItem();
        item2.setCartId(cart.getId());
        item2.setProductId(product.getId());
        item2.setQuantity(2);

        assertThatThrownBy(() -> cartItemMapper.insertItem(item2))
                .isInstanceOf(DataIntegrityViolationException.class);
    }

    @Test
    void findCartItems_returnsEmpty_forNewCart() {
        List<CartItemResponse> items = cartItemMapper.findCartItems(cart.getId());
        assertThat(items).isEmpty();
    }
}
