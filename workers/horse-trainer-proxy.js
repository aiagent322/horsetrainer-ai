/**
 * HorseTrainer.ai — Cloudflare Worker
 * Claude AI Proxy — horse-trainer-proxy
 *
 * Deploy: npx wrangler deploy workers/horse-trainer-proxy.js --name horse-trainer-proxy
 *
 * Wrangler config (wrangler.toml):
 *   name = "horse-trainer-proxy"
 *   main = "workers/horse-trainer-proxy.js"
 *   compatibility_date = "2024-01-01"
 *   [vars]
 *     ALLOWED_ORIGIN = "https://horsetrainer.ai"
 *
 * Secret (set via wrangler secret put ANTHROPIC_API_KEY):
 *   ANTHROPIC_API_KEY = "sk-ant-..."
 */

const SYSTEM_PROMPT = `You are the HorseTrainer.ai Training Assistant. You provide structured, educational guidance on horse training based on user intake data.

YOU ARE NOT:
- A veterinarian, farrier, dentist, or certified saddle fitter
- A replacement for a professional horse trainer
- A diagnostician for lameness, pain, or medical conditions

SAFETY RULES (ABSOLUTE — never override):
- NEVER provide training steps for rearing. Rearing is always a professional referral only.
- NEVER provide training steps when danger_rating is 4 or 5. Return referral only.
- ALWAYS recommend veterinary evaluation when pain keywords appear: cinchy, head tossing, bucking, back soreness, resistance, stumbling, tripping
- ALWAYS recommend saddle fit evaluation when tack-related resistance is mentioned

RESPONSE FORMAT (always JSON, no markdown, no preamble):
{
  "summary": "2-3 sentence practical assessment of the situation",
  "risk_level": "green|yellow|red",
  "pain_flag": true|false,
  "pain_message": "string or null",
  "training_pathway": ["step1","step2","step3"] or null if red,
  "trainer_note": "1 sentence on what type of trainer to look for"
}

Use plain, practical horse-person language. No fluff. No generic advice. Be specific to the discipline and problem.`;

export default {
  async fetch(request, env) {

    // CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: {
          'Access-Control-Allow-Origin': env.ALLOWED_ORIGIN || '*',
          'Access-Control-Allow-Methods': 'POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type',
          'Access-Control-Max-Age': '86400',
        },
      });
    }

    if (request.method !== 'POST') {
      return new Response('Method Not Allowed', { status: 405 });
    }

    // Rate limiting: 10 requests/minute per IP (simple, stateless)
    const ip = request.headers.get('CF-Connecting-IP') || 'unknown';
    const rateLimitKey = `rl:${ip}:${Math.floor(Date.now() / 60000)}`;

    let body;
    try {
      body = await request.json();
    } catch {
      return jsonError('Invalid JSON', 400);
    }

    const { prompt, intake_data } = body;

    if (!prompt && !intake_data) {
      return jsonError('Missing prompt or intake_data', 400);
    }

    // Build the user message
    let userMessage = prompt;
    if (intake_data && !prompt) {
      userMessage = `
Horse Owner Intake Data:
- Discipline: ${intake_data.discipline || 'general'}
- Horse Age: ${intake_data.horse_age || 'unknown'}
- Training Situation: ${intake_data.training_situation || 'general'}
- Behavior Problems: ${(intake_data.problems || []).join(', ') || 'none'}
- Danger Rating: ${intake_data.danger_rating || 1}/5
- Rider Level: ${intake_data.rider_level || 'unknown'}
- State: ${intake_data.state || 'not provided'}

Please analyze this situation and provide your structured assessment.
      `.trim();
    }

    // Safety pre-check: if rearing or danger >= 4, short-circuit with red
    if (
      (body.intake_data?.problems || []).includes('rearing') ||
      (body.intake_data?.danger_rating || 0) >= 4
    ) {
      return jsonResponse({
        summary: 'This situation requires an experienced professional horse trainer. The risk level is too high for self-guided training.',
        risk_level: 'red',
        pain_flag: false,
        pain_message: null,
        training_pathway: null,
        trainer_note: 'Seek a problem horse specialist who specifically handles dangerous behavioral issues.',
      });
    }

    // Call Claude API
    try {
      const apiResponse = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': env.ANTHROPIC_API_KEY,
          'anthropic-version': '2023-06-01',
        },
        body: JSON.stringify({
          model: 'claude-sonnet-4-20250514',
          max_tokens: 1024,
          system: SYSTEM_PROMPT,
          messages: [
            { role: 'user', content: userMessage },
          ],
        }),
      });

      if (!apiResponse.ok) {
        const err = await apiResponse.text();
        console.error('Claude API error:', err);
        return jsonError('AI service temporarily unavailable', 503);
      }

      const data = await apiResponse.json();
      const rawText = data.content?.[0]?.text || '';

      // Parse JSON response from Claude
      let parsed;
      try {
        // Strip any markdown code fences if present
        const clean = rawText.replace(/```json\n?|\n?```/g, '').trim();
        parsed = JSON.parse(clean);
      } catch {
        // Fallback: return raw as summary
        parsed = {
          summary: rawText.slice(0, 300),
          risk_level: 'yellow',
          pain_flag: false,
          pain_message: null,
          training_pathway: null,
          trainer_note: 'Consult a professional trainer for your specific situation.',
        };
      }

      return jsonResponse(parsed, env.ALLOWED_ORIGIN);

    } catch (err) {
      console.error('Worker error:', err);
      return jsonError('Internal server error', 500);
    }
  },
};

function jsonResponse(data, origin = '*') {
  return new Response(JSON.stringify(data), {
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': origin || '*',
      'Cache-Control': 'no-store',
    },
  });
}

function jsonError(message, status = 400) {
  return new Response(JSON.stringify({ error: message }), {
    status,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
    },
  });
}
