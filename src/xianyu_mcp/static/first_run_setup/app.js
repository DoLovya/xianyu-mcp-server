async function tick() {
  const res = await fetch("/status", { cache: "no-store" });
  const st = await res.json();

  const status = st.status || "unknown";
  document.getElementById("status").textContent = status;

  const dot = document.getElementById("dot");
  dot.className = "dot";
  if (status === "success" || status === "done") dot.classList.add("ok");
  else if (status === "verification_required") dot.classList.add("warn");
  else if (status === "error" || status === "expired" || status === "cancelled") dot.classList.add("err");

  document.getElementById("session").textContent = st.session_id || "-";
  document.getElementById("envWritten").textContent = st.env_written ? "已写入 .env" : "未写入";

  const error = document.getElementById("error");
  if (st.error_message) {
    error.textContent = st.error_message;
    error.classList.remove("hidden");
  } else {
    error.textContent = "";
    error.classList.add("hidden");
  }

  const qr = document.getElementById("qr");
  const qrHint = document.getElementById("qrHint");
  if (st.qr_data_url) {
    qr.src = st.qr_data_url;
    qr.classList.remove("hidden");
    qrHint.classList.add("hidden");
  } else {
    qr.removeAttribute("src");
    qr.classList.add("hidden");
    qrHint.classList.remove("hidden");
  }

  const verifyNone = document.getElementById("verifyNone");
  const verifyBox = document.getElementById("verifyBox");
  const verifyLink = document.getElementById("verifyLink");
  if (st.verification_url) {
    verifyNone.classList.add("hidden");
    verifyBox.classList.remove("hidden");
    verifyLink.textContent = st.verification_url;
    verifyLink.href = st.verification_url;
  } else {
    verifyNone.classList.remove("hidden");
    verifyBox.classList.add("hidden");
    verifyLink.textContent = "";
    verifyLink.href = "";
  }

  const faceqr = document.getElementById("faceqr");
  const faceHint = document.getElementById("faceHint");
  if (st.face_qr_data_url) {
    faceqr.src = st.face_qr_data_url;
    faceqr.classList.remove("hidden");
    faceHint.classList.add("hidden");
  } else {
    faceqr.removeAttribute("src");
    faceqr.classList.add("hidden");
    faceHint.classList.remove("hidden");
  }
}

tick();
setInterval(tick, 1000);

