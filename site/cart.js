/* GradingStamps on-site cart — localStorage + one PayPal cart-upload post
   at checkout. __PAYPAL__ and __SITE__ are injected by site/build.py.      */
(function () {
  "use strict";
  var KEY = "gs_cart";
  var BUSINESS = "__PAYPAL__";
  var SITE = "__SITE__";

  function load() {
    try { return JSON.parse(localStorage.getItem(KEY)) || {}; }
    catch (e) { return {}; }
  }
  function save(c) {
    try { localStorage.setItem(KEY, JSON.stringify(c)); } catch (e) {}
    updateBadge();
  }
  function count(c) {
    var n = 0;
    for (var k in c) n += c[k].qty;
    return n;
  }
  function money(x) { return "$" + x.toFixed(2); }

  function updateBadge() {
    var el = document.querySelector(".cart-count");
    if (!el) return;
    var n = count(load());
    el.textContent = n;
    el.hidden = n === 0;
  }

  /* ---- add-to-cart buttons (event delegation, works on every page) ---- */
  document.addEventListener("click", function (e) {
    var b = e.target.closest(".add-to-cart");
    if (!b) return;
    var c = load();
    var id = b.getAttribute("data-id");
    if (!c[id]) c[id] = { name: b.getAttribute("data-name"),
                          price: parseFloat(b.getAttribute("data-price")), qty: 0 };
    c[id].qty += 1;
    save(c);
    if (!b.dataset.orig) b.dataset.orig = b.textContent;
    b.textContent = "Added ✓";
    b.classList.add("added");
    clearTimeout(b._t);
    b._t = setTimeout(function () {
      b.textContent = b.dataset.orig;
      b.classList.remove("added");
    }, 1100);
  });

  /* ---- cart page ---- */
  var root = document.getElementById("cartRoot");

  function render() {
    var c = load();
    var ids = Object.keys(c);
    if (!ids.length) {
      root.innerHTML = '<p>Your cart is empty.</p>' +
        '<p><a class="btn" href="' + root.getAttribute("data-shop") + '">Browse the catalog</a></p>';
      return;
    }
    var total = 0;
    var rows = ids.map(function (id) {
      var it = c[id];
      var line = it.price * it.qty;
      total += line;
      return '<div class="cart-row" data-id="' + id + '">' +
        '<div class="cr-name"><b>' + it.name + '</b><span class="cr-id">№ ' + id + " · " + money(it.price) + ' each</span></div>' +
        '<div class="cr-qty">' +
          '<button class="qbtn" data-act="minus" aria-label="Remove one">−</button>' +
          '<span class="qnum">' + it.qty + "</span>" +
          '<button class="qbtn" data-act="plus" aria-label="Add one">+</button>' +
        "</div>" +
        '<div class="cr-line">' + money(line) + "</div>" +
        '<button class="cr-remove" data-act="remove" aria-label="Remove ' + it.name + '">×</button>' +
        "</div>";
    }).join("");
    root.innerHTML =
      '<div class="cart-list">' + rows + "</div>" +
      '<div class="cart-total"><span>Total</span><b>' + money(total) + "</b></div>" +
      '<p class="cart-ship">Shipping and any tax are shown on the PayPal page before you pay.</p>' +
      '<button class="btn" id="checkoutBtn">Check out with PayPal</button> ' +
      '<a class="btn ghost" href="' + root.getAttribute("data-shop") + '">Keep shopping</a>';
  }

  function checkout() {
    var c = load();
    var ids = Object.keys(c);
    if (!ids.length) return;
    var f = document.createElement("form");
    f.method = "post";
    f.action = "https://www.paypal.com/cgi-bin/webscr";
    var fields = {
      cmd: "_cart", upload: "1", business: BUSINESS,
      currency_code: "USD", no_note: "1",
      return: SITE + "/thanks/", cancel_return: SITE + "/cart/",
      shopping_url: SITE + "/shop/"
    };
    ids.forEach(function (id, i) {
      var n = i + 1;
      fields["item_name_" + n] = c[id].name + " — pre-ink teacher stamp (" + id + ")";
      fields["item_number_" + n] = id;
      fields["amount_" + n] = c[id].price.toFixed(2);
      fields["quantity_" + n] = c[id].qty;
    });
    for (var k in fields) {
      var inp = document.createElement("input");
      inp.type = "hidden";
      inp.name = k;
      inp.value = fields[k];
      f.appendChild(inp);
    }
    document.body.appendChild(f);
    f.submit();
  }

  if (root) {
    render();
    root.addEventListener("click", function (e) {
      var t = e.target;
      if (t.id === "checkoutBtn") { checkout(); return; }
      var act = t.getAttribute("data-act");
      if (!act) return;
      var row = t.closest(".cart-row");
      var id = row.getAttribute("data-id");
      var c = load();
      if (!c[id]) return;
      if (act === "plus") c[id].qty += 1;
      if (act === "minus") { c[id].qty -= 1; if (c[id].qty <= 0) delete c[id]; }
      if (act === "remove") delete c[id];
      save(c);
      render();
    });
  }

  /* ---- returning from PayPal: clear the cart ---- */
  if (document.getElementById("clearCart")) {
    try { localStorage.removeItem(KEY); } catch (e) {}
  }

  updateBadge();
})();
