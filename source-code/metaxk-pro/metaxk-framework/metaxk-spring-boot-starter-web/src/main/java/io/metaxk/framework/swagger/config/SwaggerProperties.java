package io.metaxk.framework.swagger.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;

import javax.validation.constraints.NotEmpty;

/**
 * Swagger 配置属性
 *
 * @author 万界星空科技
* https://www.metaxk.io
* open@metaxk.io
 */
@ConfigurationProperties("metaxk.swagger")
@Data
public class SwaggerProperties {

    /**
     * 标题
     */
    @NotEmpty(message = "标题不能为空")
    private String title;
    /**
     * 描述
     */
    @NotEmpty(message = "描述不能为空")
    private String description;
    /**
     * 版本
     */
    @NotEmpty(message = "版本不能为空")
    private String version;



}
