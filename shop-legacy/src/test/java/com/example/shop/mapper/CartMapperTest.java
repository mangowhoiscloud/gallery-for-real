package com.example.shop.mapper;

import com.example.shop.config.TestConfig;
import com.example.shop.domain.Cart;
import com.example.shop.domain.CartItem;
import com.example.shop.domain.Member;
import com.example.shop.domain.Product;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.junit4.SpringJUnit4ClassRunner;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static org.junit.Assert.*;

@RunWith(SpringJUnit4ClassRunner.class)
@ContextConfiguration(classes = TestConfig.class)
@Transactional
public class CartMapperTest {

    @Autowired
    private CartMapper cartMapper;

    @Autowired
    private CartItemMapper cartItemMapper;

    @Autowired
    private MemberMapper memberMapper;

    @Autowired
    private ProductMapper productMapper;

    private Long memberId;
    private Long productId;

    @Before
    public void setUp() {
        Member m = new Member();
        m.setEmail("carttest@example.com");
        m.setPassword("hashed");
        m.setName("Cart Tester");
        m.setRole(Member.Role.USER);
        memberMapper.insert(m);
        memberId = m.getId();

        Product p = new Product();
        p.setName("Test Product");
        p.setPrice(new BigDecimal("9.99"));
        p.setStockQuantity(100);
        p.setStatus(Product.Status.ACTIVE);
        productMapper.insert(p);
        productId = p.getId();
    }

    // ── Cart tests ────────────────────────────────────────────────────────────

    @Test
    public void insertCartAndSelectByMemberId() {
        Cart cart = new Cart();
        cart.setMemberId(memberId);
        cartMapper.insert(cart);

        assertNotNull("Generated key must be set", cart.getId());

        Cart found = cartMapper.selectByMemberId(memberId);
        assertNotNull(found);
        assertEquals(memberId, found.getMemberId());
        assertEquals(cart.getId(), found.getId());
        assertNotNull(found.getCreatedAt());
    }

    @Test
    public void selectByMemberIdReturnsNullWhenNoCart() {
        Cart found = cartMapper.selectByMemberId(memberId);
        assertNull(found);
    }

    @Test
    public void deleteCart() {
        Cart cart = new Cart();
        cart.setMemberId(memberId);
        cartMapper.insert(cart);

        cartMapper.delete(cart.getId());

        assertNull(cartMapper.selectByMemberId(memberId));
    }

    @Test(expected = DataIntegrityViolationException.class)
    public void duplicateCartForSameMemberFails() {
        Cart c1 = new Cart();
        c1.setMemberId(memberId);
        cartMapper.insert(c1);

        Cart c2 = new Cart();
        c2.setMemberId(memberId);
        cartMapper.insert(c2);
    }

    // ── CartItem tests ────────────────────────────────────────────────────────

    @Test
    public void insertCartItemAndSelectByCartId() {
        Cart cart = new Cart();
        cart.setMemberId(memberId);
        cartMapper.insert(cart);

        CartItem item = new CartItem();
        item.setCartId(cart.getId());
        item.setProductId(productId);
        item.setQuantity(3);
        cartItemMapper.insert(item);

        assertNotNull("Generated key must be set", item.getId());

        List<CartItem> items = cartItemMapper.selectByCartId(cart.getId());
        assertEquals(1, items.size());

        CartItem found = items.get(0);
        assertEquals(productId, found.getProductId());
        assertEquals(Integer.valueOf(3), found.getQuantity());
        assertEquals("Test Product", found.getProductName());
        assertEquals(0, new BigDecimal("9.99").compareTo(found.getUnitPrice()));
        assertEquals("ACTIVE", found.getProductStatus());
        assertNotNull(found.getCreatedAt());
    }

    @Test
    public void selectByCartIdReturnsEmptyListWhenNoItems() {
        Cart cart = new Cart();
        cart.setMemberId(memberId);
        cartMapper.insert(cart);

        List<CartItem> items = cartItemMapper.selectByCartId(cart.getId());
        assertTrue(items.isEmpty());
    }

    @Test
    public void selectCartItemById() {
        Cart cart = new Cart();
        cart.setMemberId(memberId);
        cartMapper.insert(cart);

        CartItem item = new CartItem();
        item.setCartId(cart.getId());
        item.setProductId(productId);
        item.setQuantity(2);
        cartItemMapper.insert(item);

        CartItem found = cartItemMapper.selectById(item.getId());
        assertNotNull(found);
        assertEquals(item.getId(), found.getId());
        assertEquals(Integer.valueOf(2), found.getQuantity());
        assertEquals("Test Product", found.getProductName());
    }

    @Test
    public void updateQuantity() {
        Cart cart = new Cart();
        cart.setMemberId(memberId);
        cartMapper.insert(cart);

        CartItem item = new CartItem();
        item.setCartId(cart.getId());
        item.setProductId(productId);
        item.setQuantity(1);
        cartItemMapper.insert(item);

        Map<String, Object> params = new HashMap<String, Object>();
        params.put("id", item.getId());
        params.put("quantity", 5);
        cartItemMapper.updateQuantity(params);

        CartItem updated = cartItemMapper.selectById(item.getId());
        assertEquals(Integer.valueOf(5), updated.getQuantity());
    }

    @Test
    public void deleteCartItemById() {
        Cart cart = new Cart();
        cart.setMemberId(memberId);
        cartMapper.insert(cart);

        CartItem item = new CartItem();
        item.setCartId(cart.getId());
        item.setProductId(productId);
        item.setQuantity(1);
        cartItemMapper.insert(item);

        cartItemMapper.deleteById(item.getId());

        assertNull(cartItemMapper.selectById(item.getId()));
        assertEquals(0, cartItemMapper.countByCartId(cart.getId()));
    }

    @Test
    public void deleteByCartIdClearsAllItems() {
        // add a second product
        Product p2 = new Product();
        p2.setName("Second Product");
        p2.setPrice(new BigDecimal("19.99"));
        p2.setStockQuantity(50);
        p2.setStatus(Product.Status.ACTIVE);
        productMapper.insert(p2);

        Cart cart = new Cart();
        cart.setMemberId(memberId);
        cartMapper.insert(cart);

        CartItem item1 = new CartItem();
        item1.setCartId(cart.getId());
        item1.setProductId(productId);
        item1.setQuantity(1);
        cartItemMapper.insert(item1);

        CartItem item2 = new CartItem();
        item2.setCartId(cart.getId());
        item2.setProductId(p2.getId());
        item2.setQuantity(2);
        cartItemMapper.insert(item2);

        assertEquals(2, cartItemMapper.countByCartId(cart.getId()));

        cartItemMapper.deleteByCartId(cart.getId());

        assertEquals(0, cartItemMapper.countByCartId(cart.getId()));
        assertTrue(cartItemMapper.selectByCartId(cart.getId()).isEmpty());
    }

    @Test
    public void countByCartId() {
        Cart cart = new Cart();
        cart.setMemberId(memberId);
        cartMapper.insert(cart);

        assertEquals(0, cartItemMapper.countByCartId(cart.getId()));

        CartItem item = new CartItem();
        item.setCartId(cart.getId());
        item.setProductId(productId);
        item.setQuantity(1);
        cartItemMapper.insert(item);

        assertEquals(1, cartItemMapper.countByCartId(cart.getId()));
    }

    @Test(expected = DataIntegrityViolationException.class)
    public void duplicateProductInCartFails() {
        Cart cart = new Cart();
        cart.setMemberId(memberId);
        cartMapper.insert(cart);

        CartItem item1 = new CartItem();
        item1.setCartId(cart.getId());
        item1.setProductId(productId);
        item1.setQuantity(1);
        cartItemMapper.insert(item1);

        CartItem item2 = new CartItem();
        item2.setCartId(cart.getId());
        item2.setProductId(productId);
        item2.setQuantity(2);
        cartItemMapper.insert(item2);
    }

    @Test
    public void cartItemsReflectLiveProductData() {
        // Verify JOIN returns current product name and price
        Cart cart = new Cart();
        cart.setMemberId(memberId);
        cartMapper.insert(cart);

        CartItem item = new CartItem();
        item.setCartId(cart.getId());
        item.setProductId(productId);
        item.setQuantity(2);
        cartItemMapper.insert(item);

        List<CartItem> items = cartItemMapper.selectByCartId(cart.getId());
        assertEquals("Test Product", items.get(0).getProductName());
        assertEquals(0, new BigDecimal("9.99").compareTo(items.get(0).getUnitPrice()));
        assertEquals("ACTIVE", items.get(0).getProductStatus());
    }

    @Test
    public void cartItemShowsInactiveProductStatus() {
        Product inactive = new Product();
        inactive.setName("Old Product");
        inactive.setPrice(new BigDecimal("5.00"));
        inactive.setStockQuantity(0);
        inactive.setStatus(Product.Status.INACTIVE);
        productMapper.insert(inactive);

        Cart cart = new Cart();
        cart.setMemberId(memberId);
        cartMapper.insert(cart);

        CartItem item = new CartItem();
        item.setCartId(cart.getId());
        item.setProductId(inactive.getId());
        item.setQuantity(1);
        cartItemMapper.insert(item);

        List<CartItem> items = cartItemMapper.selectByCartId(cart.getId());
        assertEquals("INACTIVE", items.get(0).getProductStatus());
    }
}
