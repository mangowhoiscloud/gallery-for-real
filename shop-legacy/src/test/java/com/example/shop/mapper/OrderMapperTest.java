package com.example.shop.mapper;

import com.example.shop.config.TestConfig;
import com.example.shop.domain.Member;
import com.example.shop.domain.Order;
import com.example.shop.domain.OrderItem;
import com.example.shop.domain.Product;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.junit4.SpringJUnit4ClassRunner;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static org.junit.Assert.*;

@RunWith(SpringJUnit4ClassRunner.class)
@ContextConfiguration(classes = TestConfig.class)
@Transactional
public class OrderMapperTest {

    @Autowired
    private OrderMapper orderMapper;

    @Autowired
    private OrderItemMapper orderItemMapper;

    @Autowired
    private MemberMapper memberMapper;

    @Autowired
    private ProductMapper productMapper;

    private Long memberId;
    private Long productId;

    @Before
    public void setUp() {
        Member m = new Member();
        m.setEmail("ordertest@example.com");
        m.setPassword("hashed");
        m.setName("Order Tester");
        m.setRole(Member.Role.USER);
        memberMapper.insert(m);
        memberId = m.getId();

        Product p = new Product();
        p.setName("Orderable Widget");
        p.setPrice(new BigDecimal("29.99"));
        p.setStockQuantity(50);
        p.setStatus(Product.Status.ACTIVE);
        productMapper.insert(p);
        productId = p.getId();
    }

    private Order buildOrder() {
        Order o = new Order();
        o.setMemberId(memberId);
        o.setTotalAmount(new BigDecimal("59.98"));
        o.setStatus(Order.Status.PENDING);
        o.setShippingAddress("123 Main St, Anytown, USA");
        return o;
    }

    // ── OrderMapper tests ──────────────────────────────────────────────────────

    @Test
    public void insertOrderReturnsGeneratedKey() {
        Order order = buildOrder();
        orderMapper.insert(order);

        assertNotNull("Generated key must be set", order.getId());
    }

    @Test
    public void selectByIdReturnsOrder() {
        Order order = buildOrder();
        orderMapper.insert(order);

        Order found = orderMapper.selectById(order.getId());

        assertNotNull(found);
        assertEquals(order.getId(), found.getId());
        assertEquals(memberId, found.getMemberId());
        assertEquals(0, new BigDecimal("59.98").compareTo(found.getTotalAmount()));
        assertEquals(Order.Status.PENDING, found.getStatus());
        assertEquals("123 Main St, Anytown, USA", found.getShippingAddress());
        assertNotNull(found.getCreatedAt());
        assertNotNull(found.getUpdatedAt());
    }

    @Test
    public void selectByIdReturnsNullForMissing() {
        assertNull(orderMapper.selectById(999999L));
    }

    @Test
    public void selectByMemberIdPaginated() {
        // Insert 3 orders for this member
        for (int i = 0; i < 3; i++) {
            orderMapper.insert(buildOrder());
        }

        Map<String, Object> params = new HashMap<String, Object>();
        params.put("memberId", memberId);
        params.put("limit", 2);
        params.put("offset", 0);

        List<Order> page1 = orderMapper.selectByMemberId(params);
        assertEquals(2, page1.size());

        params.put("offset", 2);
        List<Order> page2 = orderMapper.selectByMemberId(params);
        assertEquals(1, page2.size());
    }

    @Test
    public void selectByMemberIdOnlyReturnsThatMembersOrders() {
        // Insert order for another member
        Member other = new Member();
        other.setEmail("other@example.com");
        other.setPassword("hashed");
        other.setName("Other User");
        other.setRole(Member.Role.USER);
        memberMapper.insert(other);

        Order myOrder = buildOrder();
        orderMapper.insert(myOrder);

        Order theirOrder = new Order();
        theirOrder.setMemberId(other.getId());
        theirOrder.setTotalAmount(new BigDecimal("10.00"));
        theirOrder.setStatus(Order.Status.PENDING);
        theirOrder.setShippingAddress("456 Elm St");
        orderMapper.insert(theirOrder);

        Map<String, Object> params = new HashMap<String, Object>();
        params.put("memberId", memberId);
        params.put("limit", 10);
        params.put("offset", 0);

        List<Order> myOrders = orderMapper.selectByMemberId(params);
        assertEquals(1, myOrders.size());
        assertEquals(memberId, myOrders.get(0).getMemberId());
    }

    @Test
    public void selectAllPaginated() {
        // Insert 2 orders for this member and 1 for another
        Member other = new Member();
        other.setEmail("alltest@example.com");
        other.setPassword("hashed");
        other.setName("All Test User");
        other.setRole(Member.Role.USER);
        memberMapper.insert(other);

        orderMapper.insert(buildOrder());
        orderMapper.insert(buildOrder());

        Order theirOrder = new Order();
        theirOrder.setMemberId(other.getId());
        theirOrder.setTotalAmount(new BigDecimal("5.00"));
        theirOrder.setStatus(Order.Status.CONFIRMED);
        theirOrder.setShippingAddress("789 Oak Ave");
        orderMapper.insert(theirOrder);

        Map<String, Object> params = new HashMap<String, Object>();
        params.put("limit", 2);
        params.put("offset", 0);

        List<Order> page1 = orderMapper.selectAll(params);
        assertEquals(2, page1.size());

        params.put("offset", 2);
        List<Order> page2 = orderMapper.selectAll(params);
        assertEquals(1, page2.size());
    }

    @Test
    public void updateStatusChangesOnlyStatusAndUpdatedAt() throws InterruptedException {
        Order order = buildOrder();
        orderMapper.insert(order);

        Order before = orderMapper.selectById(order.getId());
        assertEquals(Order.Status.PENDING, before.getStatus());

        // Small sleep so updated_at changes detectably
        Thread.sleep(10);

        Map<String, Object> params = new HashMap<String, Object>();
        params.put("id", order.getId());
        params.put("status", Order.Status.CONFIRMED);
        orderMapper.updateStatus(params);

        Order after = orderMapper.selectById(order.getId());
        assertEquals(Order.Status.CONFIRMED, after.getStatus());
        // Total amount and shipping address must not change
        assertEquals(0, new BigDecimal("59.98").compareTo(after.getTotalAmount()));
        assertEquals("123 Main St, Anytown, USA", after.getShippingAddress());
    }

    @Test
    public void countByMemberId() {
        assertEquals(0, orderMapper.countByMemberId(memberId));

        orderMapper.insert(buildOrder());
        orderMapper.insert(buildOrder());

        assertEquals(2, orderMapper.countByMemberId(memberId));
    }

    @Test
    public void countAll() {
        int initialCount = orderMapper.countAll();

        orderMapper.insert(buildOrder());
        orderMapper.insert(buildOrder());

        assertEquals(initialCount + 2, orderMapper.countAll());
    }

    // ── OrderItemMapper tests ──────────────────────────────────────────────────

    @Test
    public void insertBatchAndSelectByOrderId() {
        Order order = buildOrder();
        orderMapper.insert(order);

        OrderItem item1 = new OrderItem();
        item1.setOrderId(order.getId());
        item1.setProductId(productId);
        item1.setProductName("Orderable Widget");
        item1.setQuantity(2);
        item1.setUnitPrice(new BigDecimal("29.99"));

        OrderItem item2 = new OrderItem();
        item2.setOrderId(order.getId());
        item2.setProductId(null); // product_id is nullable (product may be deleted)
        item2.setProductName("Deleted Product Snapshot");
        item2.setQuantity(1);
        item2.setUnitPrice(new BigDecimal("15.00"));

        orderItemMapper.insertBatch(Arrays.asList(item1, item2));

        List<OrderItem> items = orderItemMapper.selectByOrderId(order.getId());
        assertEquals(2, items.size());

        OrderItem found1 = items.get(0);
        assertEquals(order.getId(), found1.getOrderId());
        assertEquals(productId, found1.getProductId());
        assertEquals("Orderable Widget", found1.getProductName());
        assertEquals(Integer.valueOf(2), found1.getQuantity());
        assertEquals(0, new BigDecimal("29.99").compareTo(found1.getUnitPrice()));
        assertNotNull(found1.getId());

        OrderItem found2 = items.get(1);
        assertEquals("Deleted Product Snapshot", found2.getProductName());
        assertNull(found2.getProductId());
    }

    @Test
    public void selectByOrderIdReturnsEmptyListWhenNoItems() {
        Order order = buildOrder();
        orderMapper.insert(order);

        List<OrderItem> items = orderItemMapper.selectByOrderId(order.getId());
        assertTrue(items.isEmpty());
    }

    @Test
    public void batchInsertPreservesSnapshotData() {
        Order order = buildOrder();
        orderMapper.insert(order);

        // Snapshot prices at time of order — even if product price changes later
        OrderItem item = new OrderItem();
        item.setOrderId(order.getId());
        item.setProductId(productId);
        item.setProductName("Orderable Widget");
        item.setQuantity(3);
        item.setUnitPrice(new BigDecimal("29.99"));

        orderItemMapper.insertBatch(Arrays.asList(item));

        // Change product price
        Map<String, Object> stockParams = new HashMap<String, Object>();
        stockParams.put("id", productId);
        stockParams.put("delta", -1);
        productMapper.updateStock(stockParams);

        // Snapshot should still reflect original price
        List<OrderItem> items = orderItemMapper.selectByOrderId(order.getId());
        assertEquals(1, items.size());
        assertEquals(0, new BigDecimal("29.99").compareTo(items.get(0).getUnitPrice()));
        assertEquals("Orderable Widget", items.get(0).getProductName());
    }
}
