const SUPABASE_URL = "https://vxthhдcyttrzbqwequhn.supabase.co";
const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ4dGhoZGN5dHRyemJxd2VxdWhuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUyOTQzODQsImV4cCI6MjA5MDg3MDM4NH0.iVl8Nvsth9vniP2ue6hqWzlOnsade8_qxGrOmizJbHY";

async function fetchPlans(countryCode = "JP", limit = 20) {
  const url = `${SUPABASE_URL}/rest/v1/esim_plans?country_code=eq.${countryCode}&order=price_usd.asc&limit=${limit}`;
  const res = await fetch(url, {
    headers: {
      "apikey": SUPABASE_ANON_KEY,
      "Authorization": `Bearer ${SUPABASE_ANON_KEY}`
    }
  });
  return res.json();
}

fetchPlans("JP").then(plans => {
  console.log("일본 플랜:", plans.length, "개");
  console.log(plans[0]);
});
