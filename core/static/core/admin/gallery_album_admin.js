(function () {
  function toggleSliderFields() {
    const checkbox = document.getElementById("id_show_on_homepage_slider");
    const captionRow = document.querySelector(".form-row.field-slider_caption, .field-slider_caption");
    const orderRow = document.querySelector(".form-row.field-slider_order, .field-slider_order");
    if (!checkbox) return;

    const visible = checkbox.checked;
    [captionRow, orderRow].forEach((row) => {
      if (!row) return;
      row.style.display = visible ? "" : "none";
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    const checkbox = document.getElementById("id_show_on_homepage_slider");
    if (!checkbox) return;
    toggleSliderFields();
    checkbox.addEventListener("change", toggleSliderFields);
  });
})();
