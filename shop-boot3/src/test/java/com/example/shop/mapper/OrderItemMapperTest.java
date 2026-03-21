package com.example.shop.mapper;

import com.example.shop.dto.OrderItemResponse;
import com.example.shop.entity.*;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest
@ActiveProfiles("test")
@Transactional
class OrderItemMapperTest {

    @Autowired OrderItemMapper orderItemMapper;
    @Autowired OrderMapper     orderMapper;
    @Autowired MemberMapper    memberMapper;
    @Autowired ProductMapper   productMapper;

    private Order order;
    private Product product;

    @BeforeEach
    void setUp() {
        Member member = new Member();
        member.setEmail("orderitem-test@example.com");
        member.setPassword("hashed");
        member.setName("OrderItem Tester");
        member.setPhone("01033334444");
        member.setAddress("Incheon");
        member.setRole(MemberRole.USER);
        member.setActive(true);
        memberMapper.insert(member);

        product = new Product();
        product.setName("Sample Product");
        product.setDescription("For order item test");
        product.setPrice(new BigDecimal("15.00"));
        product.setStockQuantity(200);
        product.setCategory("Misc");
        product.setImageUrl("https://example.com/img/sample.jpg");
        product.setStatus(ProductStatus.ACTIVE);
        productMapper.insert(product);

        order = new Order();
        order.setMemberId(member.getId());
        order.setTotalAmount(new BigDecimal("75.00"));
        order.setStatus(OrderStatus.PENDING);
        order.setShippingAddress("99 Test Lane");
        orderMapper.insertOrder(order);
    }

    @Test
    void batchInsertItems_andFindByOrderId() {
        OrderItem item1 = new OrderItem();
        item1.setOrderId(order.getId());
        item1.setProductId(product.getId());
        item1.setProductName("Sample Product");
        item1.setQuantity(3);
        item1.setUnitPrice(new BigDecimal("15.00"));
        orderItemMapper.insertOrderItem(item1);

        OrderItem item2 = new OrderItem();
        item2.setOrderId(order.getId());
        item2.setProductId(product.getId());
        item2.setProductName("Sample Product v2");
        item2.setQuantity(2);
        item2.setUnitPrice(new BigDecimal("15.00"));
        orderItemMapper.insertOrderItem(item2);

        assertThat(item1.getId()).isNotNull();
        assertThat(item2.getId()).isNotNull();
        assertThat(item1.getId()).isNotEqualTo(item2.getId());

        List<OrderItemResponse> items = orderItemMapper.findByOrderId(order.getId());
        assertThat(items).hasSize(2);

        OrderItemResponse resp1 = items.get(0);
        assertThat(resp1.id()).isEqualTo(item1.getId());
        assertThat(resp1.orderId()).isEqualTo(order.getId());
        assertThat(resp1.productId()).isEqualTo(product.getId());
        assertThat(resp1.productName()).isEqualTo("Sample Product");
        assertThat(resp1.quantity()).isEqualTo(3);
        assertThat(resp1.unitPrice()).isEqualByComparingTo(new BigDecimal("15.00"));

        OrderItemResponse resp2 = items.get(1);
        assertThat(resp2.productName()).isEqualTo("Sample Product v2");
        assertThat(resp2.quantity()).isEqualTo(2);
    }

    @Test
    void findByOrderId_returnsEmpty_forOrderWithNoItems() {
        List<OrderItemResponse> items = orderItemMapper.findByOrderId(order.getId());
        assertThat(items).isEmpty();
    }

    @Test
    void snapshotProductName_preservedIndependentOfProductRow() {
        // productName in order_item is a snapshot — not a FK join to product.name
        OrderItem item = new OrderItem();
        item.setOrderId(order.getId());
        item.setProductId(product.getId());
        item.setProductName("Snapshot Name At Order Time");
        item.setQuantity(1);
        item.setUnitPrice(new BigDecimal("10.00"));
        orderItemMapper.insertOrderItem(item);

        List<OrderItemResponse> items = orderItemMapper.findByOrderId(order.getId());
        assertThat(items).hasSize(1);
        assertThat(items.get(0).productName()).isEqualTo("Snapshot Name At Order Time");
    }
}
