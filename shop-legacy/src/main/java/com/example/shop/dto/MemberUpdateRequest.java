package com.example.shop.dto;

import javax.validation.constraints.Size;

public class MemberUpdateRequest {

    @Size(min = 1, max = 50)
    private String name;

    @Size(min = 8)
    private String password;

    @Size(min = 10, max = 15)
    private String phone;

    @Size(max = 200)
    private String address;

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getPassword() { return password; }
    public void setPassword(String password) { this.password = password; }

    public String getPhone() { return phone; }
    public void setPhone(String phone) { this.phone = phone; }

    public String getAddress() { return address; }
    public void setAddress(String address) { this.address = address; }
}
