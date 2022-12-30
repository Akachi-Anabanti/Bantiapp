var today = new Date();
var country = "NG";
const settings = {
  async: true,
  url: `https://public-holiday.p.rapidapi.com/2023/${country}`,
  method: "GET",
  headers: {
    "X-RapidAPI-Key": "f9193e0f25msha75dc8dacfd3fcap1dce78jsnc2fb2855c86a",
    "X-RapidAPI-Host": "public-holiday.p.rapidapi.com",
  },
};

$(function () {
  $.ajax(settings).done(function (response) {
    console.log(response);
    const nameOfHoliday = document.getElementById("NameOfHoliday");
    const holidayImage = document.getElementById("holidayImage");
    const dayOfHoliday = document.getElementById("dayOfHoliday");
    for (let i = 0; i < response.length; i++) {
      let holiday = new Date(response[i].date);
      if (holiday >= today) {
        // console.log(holiday);
        imgUrl = `https://source.unsplash.com/random/?${response[i].name}`;
        nameOfHoliday.innerText = response[i].name;
        holidayImage.src = imgUrl;
        holidayImage.style.width = "100%";
        holidayImage.style.height = "50%";
        holidayImage.alt = response[i].name;
        dayOfHoliday.innerText = moment(holiday).fromNow();
        break;
      }
    }
  });
});

// $(function () {
//   $.getJSON("http://freegeoip.net/json/", function (data) {
//     var ip = data.ip;
//     var country = data.country_name;
//     console.log(country);
//   });
// });
