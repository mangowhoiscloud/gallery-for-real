package com.example.shop.mapper;

import com.example.shop.entity.Cart;
import com.example.shop.entity.Member;
import com.example.shop.entity.MemberRole;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.transaction.annotation.Transactional;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest
@ActiveProfiles("test")
@Transactional
class CartMapperTest {

    @Autowired
    CartMapper cartMapper;

    @Autowired
    MemberMapper memberMapper;

    private Member insertMember(String email) {
        Member m = new Member();
        m.setEmail(email);
        m.setPassword("hashed");
        m.setName("Test User");
        m.setPhone("01012345678");
        m.setAddress("Seoul");
        m.setRole(MemberRole.USER);
        m.setActive(true);
        memberMapper.insert(m);
        return m;
    }

    @Test
    void insertCart_andFindByMemberId() {
        Member member = insertMember("cart-test@example.com");

        Cart cart = new Cart();
        cart.setMemberId(member.getId());
        cartMapper.insertCart(cart);

        assertThat(cart.getId()).isNotNull();

        Cart found = cartMapper.findByMemberId(member.getId());
        assertThat(found).isNotNull();
        assertThat(found.getMemberId()).isEqualTo(member.getId());
        assertThat(found.getCreatedAt()).isNotNull();
        assertThat(found.getUpdatedAt()).isNotNull();
    }

    @Test
    void findByMemberId_returnsNull_whenNoCart() {
        Member member = insertMember("no-cart@example.com");

        Cart found = cartMapper.findByMemberId(member.getId());
        assertThat(found).isNull();
    }
}
