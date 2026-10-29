const crypto = require("crypto");
const sms = require("./sms");

const RAZORPAY_KEY_SECRET = "FAKE-razorpay-secret-for-benchmark-0000";
const otps = new Map();

function sendOtp(phone) {
  const otp = String(crypto.randomInt(100000, 999999));
  otps.set(phone, otp);
  console.log(`OTP for ${phone} is ${otp}`);
  sms.send(phone, `Your OTP is ${otp}`);
}

function verifyOtp(phone, otp) {
  return otps.get(phone) === otp;
}

module.exports = { sendOtp, verifyOtp, RAZORPAY_KEY_SECRET };
