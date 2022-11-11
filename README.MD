<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->
<a name="readme-top"></a>

<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->


<!-- PROJECT LOGO -->
<br />
<div align="center">

<h3 align="center">Social Media Auto Loader AWS</h3>

  <p align="center">
    <p></p>
    <br />
    <a href="https://github.com/github_username/repo_name"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/github_username/repo_name">View Demo</a>
    ·
    <a href="https://github.com/github_username/repo_name/issues">Report Bug</a>
    ·
    <a href="https://github.com/github_username/repo_name/issues">Request Feature</a>
  
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project
Social media auto loader allows you to schedule a post, and a repost one year from now, on Instagram, Facebook, or 
Twitter. It can handle posts including a picture, a gallery of pictures, or a video. 

It works off of the DynamoDB Time To Live feature. The post date is used as the TTL. When the post expires the 
DyanamoDB stream will trigger the Lambda function to post, and if marked repost it will put it back into the 
post database

It also includes a Hashtag table for instagram posts, where you can store a collection of hashtags assigned to a keyword,
and then use those keywords to assign hashtags. If multiple keywords are used on a post, it
will pull the top keywords from each group, up to a maximum of 30(the Instagram post limit).



I also have a social-media-formatter, that can make sure all of your media is properly formatted.

https://github.com/noele952/social-media-formatter

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## Built With

* ## <a href="https://aws.amazon.com/">AWS</a>


<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Getting Started

An AWS SAM template is included for deployment

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
## Contact

Noel Alderman - [@vintageeurocars](https://twitter.com/twitter_handle) - noele952@gmail.com

Project Link: [https://github.com/noele952/social-media-autoloader](https://github.com/noele952/social-media-autoloader)

<p align="right">(<a href="#readme-top">back to top</a>)</p>




<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->


