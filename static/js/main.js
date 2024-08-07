$(document).ready(function () {
    // Smooth scrolling when clicking on navbar links
    $('a[href^="#"]').on("click", function (e) {
      e.preventDefault();
      var target = this.hash;
      var $target = $(target);
  
      if ($target.length) {
        $("html, body")
          .stop()
          .animate(
            {
              scrollTop: $target.offset().top,
            },
            1000,
            "swing",
            function () {
              window.location.hash = target;
            }
          );
      }
    });
  
    // Spinner
    var spinner = function () {
      setTimeout(function () {
        if ($("#spinner").length > 0) {
          $("#spinner").removeClass("show");
        }
      }, 1);
    };
    spinner();
  
    // Initiate the wowjs
    new WOW().init();
  
    // Fixed Navbar
    $(window).scroll(function () {
      if ($(window).width() < 992) {
        if ($(this).scrollTop() > 45) {
          $(".fixed-top").addClass("bg-white shadow");
        } else {
          $(".fixed-top").removeClass("bg-white shadow");
        }
      } else {
        if ($(this).scrollTop() > 45) {
          $(".fixed-top").addClass("bg-white shadow").css("top", -45);
        } else {
          $(".fixed-top").removeClass("bg-white shadow").css("top", 0);
        }
      }
    });
  
    // Back to top button
    $(window).scroll(function () {
      if ($(this).scrollTop() > 300) {
        $(".back-to-top").fadeIn("slow");
      } else {
        $(".back-to-top").fadeOut("slow");
      }
    });
    $(".back-to-top").click(function () {
      $("html, body").animate({ scrollTop: 0 }, 1500, "easeInOutExpo");
      return false;
    });
  
    // Testimonials carousel
    $(".testimonial-carousel").owlCarousel({
      autoplay: true,
      smartSpeed: 1000,
      margin: 25,
      loop: true,
      center: true,
      dots: false,
      nav: true,
      navText: [
        '<i class="bi bi-chevron-left"></i>',
        '<i class="bi bi-chevron-right"></i>',
      ],
      responsive: {
        0: {
          items: 1,
        },
        768: {
          items: 2,
        },
        992: {
          items: 3,
        },
      },
    });
  });
  
  var form = document.getElementById("my-form");
    async function handleSubmit(event) {
    event.preventDefault();
    var data = new FormData(event.target);
    fetch(event.target.action, {
        method: form.method,
        body: data,
        headers: {
        'Accept': 'application/json'
        }
    }).then(response => {
        // Setelah formulir berhasil dikirim, refresh halaman
        location.reload();
    }).catch(error => {
        // Jika ada kesalahan, Anda masih dapat memilih untuk merefresh halaman atau menampilkan pesan kesalahan
        location.reload();
    });
    }

    form.addEventListener("submit", handleSubmit);