---
layout: project
title: 'Spring'
image: /assets/img/categories/spring.png
screenshot: /assets/img/categories/spring.png
caption: Spring use cases for every day development
description: >
 The Spring Framework is an application framework and inversion of control container for the Java platform.
 Spring is a powerful, lightweight framework used for application development. 
---

{% assign posts = site.categories[page.slug] | default:site.tags[page.slug] | default:site.posts %}

{% if page.title.size > 0 %}
  <header>
   
  <hr class="sr-only"/>
{% endif %}


{% assign date_formats  = site.data.strings.date_formats               %}
{% assign list_group_by = date_formats.list_group_by | default:"%Y"    %}
{% assign list_entry    = date_formats.list_entry    | default:"%d %b" %}

{% for post in posts %}
  {% assign currentdate = post.date | date:list_group_by %}
  {% if currentdate != date %}
    {% unless forloop.first %}</ul>{% endunless %}
    <h2 id="{{ list_group_by | slugify }}-{{ currentdate | slugify }}" class="hr">{{ currentdate }}</h2>
    <ul class="related-posts">
    {% assign date = currentdate %}
  {% endif %}
  {% include components/post-list-item.html post=post format=list_entry %}
  {% if forloop.last %}</ul>{% endif %}
{% endfor %}