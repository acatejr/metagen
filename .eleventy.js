module.exports = function(eleventyConfig) {
  eleventyConfig.setServerOptions({
    host: "0.0.0.0"
  });

  return {
    dir: {
      input: "docs",
      output: "_site",
      includes: "_includes",
      data: "_data"
    },
    markdownTemplateEngine: "njk"
  };
};
