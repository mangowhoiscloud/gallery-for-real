package com.example.shop.dto;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.Test;

import java.util.Arrays;
import java.util.List;

import static org.junit.Assert.*;

public class PageResponseTest {

    private final ObjectMapper mapper = new ObjectMapper();

    @Test
    public void totalPagesCalculatedCorrectly() {
        List<String> content = Arrays.asList("a", "b", "c");
        PageResponse<String> page = new PageResponse<String>(content, 25, 0, 10);

        assertEquals(3, page.getTotalPages());
        assertEquals(25, page.getTotalElements());
        assertEquals(0, page.getCurrentPage());
        assertEquals(10, page.getSize());
        assertEquals(content, page.getContent());
    }

    @Test
    public void totalPagesRoundsUp() {
        PageResponse<String> page = new PageResponse<String>(Arrays.asList("x"), 11, 1, 10);
        assertEquals(2, page.getTotalPages());
    }

    @Test
    public void totalPagesZeroWhenSizeZero() {
        PageResponse<String> page = new PageResponse<String>(Arrays.asList("x"), 5, 0, 0);
        assertEquals(0, page.getTotalPages());
    }

    @Test
    public void serializesToJson() throws Exception {
        List<Integer> items = Arrays.asList(1, 2, 3);
        PageResponse<Integer> page = new PageResponse<Integer>(items, 30, 2, 10);

        String json = mapper.writeValueAsString(page);

        assertTrue(json.contains("\"totalPages\":3"));
        assertTrue(json.contains("\"totalElements\":30"));
        assertTrue(json.contains("\"currentPage\":2"));
        assertTrue(json.contains("\"size\":10"));
        assertTrue(json.contains("\"content\":[1,2,3]"));
    }

    @Test
    public void deserializesFromJson() throws Exception {
        String json = "{\"content\":[\"foo\",\"bar\"],\"totalPages\":5,\"totalElements\":50,\"currentPage\":1,\"size\":10}";
        PageResponse page = mapper.readValue(json, PageResponse.class);

        assertEquals(5, page.getTotalPages());
        assertEquals(50L, page.getTotalElements());
        assertEquals(1, page.getCurrentPage());
        assertEquals(10, page.getSize());
    }
}
