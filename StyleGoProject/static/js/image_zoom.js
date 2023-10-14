//document.addEventListener('DOMContentLoaded', function () {
//    // Initialize imageZoom for each image in the carousel
//    {% for image in products.images.all %}
//    imageZoom('image{{ forloop.counter }}', 'lens{{ forloop.counter }}');
//    {% endfor %}
//});
//
//function imageZoom(imgID, lensID) {
//    let img = document.getElementById(imgID);
//    let lens = document.getElementById(lensID);
//    lens.style.backgroundImage = `url(${img.src})`;
//
//    let ratio = 3;
//
//    lens.style.backgroundSize = (img.width * ratio) + 'px ' + (img.height * ratio) + 'px';
//
//    img.addEventListener("mousemove", moveLens);
//    lens.addEventListener("mousemove", moveLens);
//    img.addEventListener("touchmove", moveLens);
//
//    function moveLens(e) {
//        let pos = getCursor();
//
//        let positionLeft = pos.x - (lens.offsetWidth / 2);
//        let positionTop = pos.y - (lens.offsetHeight / 2);
//
//        if (positionLeft < 0) {
//            positionLeft = 0;
//        }
//
//        if (positionTop < 0) {
//            positionTop = 0;
//        }
//
//        if (positionLeft > img.width - lens.offsetWidth / 3) {
//            positionLeft = img.width - lens.offsetWidth / 3;
//        }
//
//        if (positionTop > img.height - lens.offsetHeight / 3) {
//            positionTop = img.height - lens.offsetHeight / 3;
//        }
//
//        lens.style.left = positionLeft + 'px';
//        lens.style.top = positionTop + 'px';
//
//        lens.style.backgroundPosition = "-" + (pos.x * ratio) + 'px -' + (pos.y * ratio) + 'px';
//    }
//
//    function getCursor() {
//        let e = window.event;
//        let bounds = img.getBoundingClientRect();
//        let x = e.pageX - bounds.left;
//        let y = e.pageY - bounds.top;
//        x = x - window.pageXOffset;
//        y = y - window.pageYOffset;
//        return { 'x': x, 'y': y };
//    }
//}
