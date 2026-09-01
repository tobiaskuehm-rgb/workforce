#!/usr/bin/env ruby

# NIE AUSGEFUEHRT. Stand 2026-09-02 nennt kein Nachweis unter evidence/ einen
# Lauf dieses Skripts, und kein Runbook ruft es auf (review finding G-046).
#
# Es braucht drei Dinge, die es heute alle nicht gibt: drei echte Bearer-Token,
# einen Kanal auf TESTING statt DISABLED, und HTTPS-Erreichbarkeit von aussen
# (Port 8443, DSM-Firewall). Jedes davon ist ein eigener freigabepflichtiger
# Schritt, also ist ein Lauf ein eigenes Fenster und kein Nebenbei.
#
# Das steht hier, weil der Code an zwei Stellen mit diesem Skript argumentiert:
# app.py begruendet damit, dass /openapi.json authentifiziert statt entfernt
# wurde, und REVIEW_ANTWORTEN.md fuehrt es als Grund an. Beides haelt nur, wenn
# daneben steht, dass die Pruefung bislang eine Moeglichkeit ist und kein Beleg.

require "json"
require "io/console"
require "net/http"
require "openssl"
require "uri"

BASE_URL = ENV.fetch("BUS_E2E_BASE_URL", "https://192-168-68-77.k30068872219.direct.quickconnect.to:8443")
token_names = %w[BUS_E2E_TOKEN_KARL BUS_E2E_TOKEN_GERD BUS_E2E_TOKEN_NORA]
token_values = token_names.map { |name| ENV[name] }
if token_values.any? { |token| token.nil? || token.empty? }
  reader = proc do |_input = nil|
    3.times.map do
      line = STDIN.gets
      raise "Three acceptance tokens are required on standard input" unless line

      line.strip
    end
  end
  token_values = STDIN.tty? ? STDIN.noecho(&reader) : reader.call
end
TOKENS = { karl: token_values[0], gerd: token_values[1], nora: token_values[2] }.freeze
token_names.each { |name| ENV.delete(name) }

uri = URI(BASE_URL)
raise "BUS_E2E_BASE_URL must use https" unless uri.is_a?(URI::HTTPS)
raise "Acceptance tokens are malformed" unless TOKENS.values.all? { |token| token.length.between?(32, 512) }

RUN = ENV.fetch("BUS_E2E_RUN_ID", Time.now.utc.strftime("%Y%m%d-%H%M%S"))
raise "BUS_E2E_RUN_ID is malformed" unless RUN.match?(/\A[A-Z0-9-]{6,32}\z/)

REQUEST_PREFIX = "REQ-API-E2E-#{RUN}"
IDEMPOTENCY_PREFIX = "IDEM-API-E2E-#{RUN}"
TASK_ID = "ENG-E2E-#{RUN}"
HANDOFF_ID = "HO-E2E-#{RUN}"

def request(http, method, path, token: nil, api_key: nil, request_id: nil, idempotency_key: nil, body: nil)
  request_class = {
    get: Net::HTTP::Get,
    post: Net::HTTP::Post
  }.fetch(method)
  req = request_class.new(path)
  req["Authorization"] = "Bearer #{token}" if token
  # The schema route moved behind the API key (review finding G-040). It is
  # the only call here that authenticates this way; the bus routes use bearer
  # tokens and know nothing about this header.
  req["X-API-Key"] = api_key if api_key
  req["X-Request-ID"] = request_id if request_id
  req["Idempotency-Key"] = idempotency_key if idempotency_key
  if body
    req["Content-Type"] = "application/json"
    req.body = JSON.generate(body)
  end
  response = http.request(req)
  parsed = response.body.nil? || response.body.empty? ? nil : JSON.parse(response.body)
  [response.code.to_i, parsed]
end

def expect(code, expected, payload, label)
  return payload if code == expected

  detail = payload.is_a?(Hash) ? payload["detail"] : nil
  raise "#{label}: expected HTTP #{expected}, got #{code}#{detail ? " (#{detail})" : ""}"
end

def expect_detail(code, expected_code, payload, expected_detail, label)
  expect(code, expected_code, payload, label)
  raise "#{label}: expected #{expected_detail}" unless payload == { "detail" => expected_detail }
end

def contains?(items, key, value)
  items.any? { |item| item[key] == value }
end

http = Net::HTTP.new(uri.host, uri.port)
http.use_ssl = true
http.verify_mode = OpenSSL::SSL::VERIFY_PEER
http.open_timeout = 10
http.read_timeout = 15

summary = {}

http.start do |client|
  karl_message = {
    recipient_id: "AI-ENG-001",
    subject: "API-E2E Technikstatus",
    body: "Bitte den realen HTTPS-Ende-zu-Ende-Test pruefen.",
    action_class: "INTERNAL_REVIEW",
    confidentiality: "NEED_TO_KNOW",
    task_ref: "ENG-003",
    handoff_ref: "HO-020",
    parent_message_id: nil
  }

  code, first = request(
    client, :post, "/bus/v1/messages",
    token: TOKENS[:karl],
    request_id: "#{REQUEST_PREFIX}-KARL-GERD-1",
    idempotency_key: "#{IDEMPOTENCY_PREFIX}-KARL-GERD-1",
    body: karl_message
  )
  expect(code, 201, first, "Karl -> Gerd")
  raise "Karl sender identity mismatch" unless first["sender_id"] == "SAO-001"
  raise "Gerd recipient mismatch" unless first["recipient_id"] == "AI-ENG-001"
  raise "Initial delivery mismatch" unless first["delivery_status"] == "DELIVERED" && first["hop_count"] == 0
  message_1 = first.fetch("message_id")

  code, retry_message = request(
    client, :post, "/bus/v1/messages",
    token: TOKENS[:karl],
    request_id: "#{REQUEST_PREFIX}-KARL-GERD-RETRY",
    idempotency_key: "#{IDEMPOTENCY_PREFIX}-KARL-GERD-1",
    body: karl_message
  )
  expect(code, 201, retry_message, "Idempotent message retry")
  raise "Idempotent retry changed message identity" unless retry_message["message_id"] == message_1

  code, gerd_inbox = request(client, :get, "/bus/v1/messages?scope=INBOX&limit=100", token: TOKENS[:gerd])
  expect(code, 200, gerd_inbox, "Gerd inbox")
  raise "Gerd inbox lacks Karl message" unless contains?(gerd_inbox, "message_id", message_1)

  code, acknowledged = request(
    client, :post, "/bus/v1/messages/#{message_1}/ack",
    token: TOKENS[:gerd],
    request_id: "#{REQUEST_PREFIX}-GERD-ACK-1",
    body: { decision: "ACCEPTED", note: "Technische Pruefung uebernommen." }
  )
  expect(code, 200, acknowledged, "Gerd acknowledgement")
  raise "Acknowledgement was not recorded" unless acknowledged["delivery_status"] == "ACCEPTED" && acknowledged["accepted_at"]

  code, reply = request(
    client, :post, "/bus/v1/messages",
    token: TOKENS[:gerd],
    request_id: "#{REQUEST_PREFIX}-GERD-KARL-1",
    idempotency_key: "#{IDEMPOTENCY_PREFIX}-GERD-KARL-1",
    body: {
      recipient_id: "SAO-001",
      subject: "API-E2E Technikstatus angenommen",
      body: "Die technische Pruefung laeuft.",
      action_class: "INTERNAL_STATUS",
      confidentiality: "NEED_TO_KNOW",
      task_ref: "ENG-003",
      handoff_ref: "HO-020",
      parent_message_id: message_1
    }
  )
  expect(code, 201, reply, "Gerd -> Karl reply")
  raise "Reply correlation mismatch" unless reply["correlation_id"] == message_1 && reply["hop_count"] == 1
  reply_1 = reply.fetch("message_id")

  code, karl_inbox = request(client, :get, "/bus/v1/messages?scope=INBOX&limit=100", token: TOKENS[:karl])
  expect(code, 200, karl_inbox, "Karl inbox")
  raise "Karl inbox lacks Gerd reply" unless contains?(karl_inbox, "message_id", reply_1)

  code, task = request(
    client, :post, "/bus/v1/tasks",
    token: TOKENS[:karl],
    request_id: "#{REQUEST_PREFIX}-TASK-CREATE",
    body: {
      task_id: TASK_ID,
      owner_id: "AI-ENG-001",
      task_status: "OPEN",
      priority: "HIGH",
      title: "Realen Workforce-Bus API-E2E pruefen",
      expected_output: "HTTPS-, Zustell-, Annahme-, Antwort-, Audit- und Fail-closed-Nachweis",
      source_ref: "DEC-016/ENG-003/E2E-2026-08-14-2",
      review_at: nil
    }
  )
  expect(code, 201, task, "Task creation")
  raise "Task coordination mismatch" unless task["creator_id"] == "SAO-001" && task["owner_id"] == "AI-ENG-001" && task["task_status"] == "OPEN"

  %w[IN_PROGRESS REVIEW].each do |new_status|
    code, task = request(
      client, :post, "/bus/v1/tasks/#{TASK_ID}/transition",
      token: TOKENS[:gerd],
      request_id: "#{REQUEST_PREFIX}-TASK-#{new_status}",
      body: { new_status: new_status, completion_evidence: nil }
    )
    expect(code, 200, task, "Task transition #{new_status}")
  end

  code, handoff = request(
    client, :post, "/bus/v1/handoffs",
    token: TOKENS[:gerd],
    request_id: "#{REQUEST_PREFIX}-HANDOFF-CREATE",
    body: {
      handoff_id: HANDOFF_ID,
      recipient_id: "EAC-001",
      handoff_status: "OPEN",
      input_summary: "Technischer API-E2E-Status und offene Abschlussnachweise.",
      expected_output: "Closed-Loop-Nachhalten bis zum dokumentierten Testergebnis.",
      source_ref: "DEC-016/ENG-003/E2E-2026-08-14-2",
      task_ref: TASK_ID,
      risks_and_assumptions: "Keine externe oder privilegierte Aktion.",
      trigger_or_due: "Nach technischem Testlauf"
    }
  )
  expect(code, 201, handoff, "Gerd -> Nora handoff")
  raise "Handoff identity mismatch" unless handoff["sender_id"] == "AI-ENG-001" && handoff["recipient_id"] == "EAC-001"

  code, nora_handoffs = request(client, :get, "/bus/v1/handoffs?scope=INBOX&limit=100", token: TOKENS[:nora])
  expect(code, 200, nora_handoffs, "Nora handoff inbox")
  raise "Nora inbox lacks handoff" unless contains?(nora_handoffs, "handoff_id", HANDOFF_ID)

  code, handoff = request(
    client, :post, "/bus/v1/handoffs/#{HANDOFF_ID}/transition",
    token: TOKENS[:nora],
    request_id: "#{REQUEST_PREFIX}-HANDOFF-ACCEPT",
    body: { new_status: "ACCEPTED", response_note: "Administratives Closed Loop uebernommen." }
  )
  expect(code, 200, handoff, "Nora handoff acceptance")
  raise "Handoff acceptance mismatch" unless handoff["handoff_status"] == "ACCEPTED" && handoff["accepted_at"]

  code, nora_message = request(
    client, :post, "/bus/v1/messages",
    token: TOKENS[:nora],
    request_id: "#{REQUEST_PREFIX}-NORA-GERD-1",
    idempotency_key: "#{IDEMPOTENCY_PREFIX}-NORA-GERD-1",
    body: {
      recipient_id: "AI-ENG-001",
      subject: "API-E2E Handoff angenommen",
      body: "Closed Loop ist eroeffnet; keine externe Aktion wurde ausgeloest.",
      action_class: "INTERNAL_COORDINATION",
      confidentiality: "PROJECT_INTERNAL",
      task_ref: TASK_ID,
      handoff_ref: HANDOFF_ID,
      parent_message_id: nil
    }
  )
  expect(code, 201, nora_message, "Nora -> Gerd message")
  raise "Nora sender identity mismatch" unless nora_message["sender_id"] == "EAC-001" && nora_message["recipient_id"] == "AI-ENG-001"
  nora_message_id = nora_message.fetch("message_id")

  code, gerd_inbox = request(client, :get, "/bus/v1/messages?scope=INBOX&limit=100", token: TOKENS[:gerd])
  expect(code, 200, gerd_inbox, "Gerd inbox after Nora message")
  raise "Gerd inbox lacks Nora message" unless contains?(gerd_inbox, "message_id", nora_message_id)

  code, karl_project = request(client, :get, "/bus/v1/messages?scope=PROJECT&limit=100", token: TOKENS[:karl])
  expect(code, 200, karl_project, "Karl project view")
  raise "Karl project view lacks project-internal Nora message" unless contains?(karl_project, "message_id", nora_message_id)

  code, nora_project = request(client, :get, "/bus/v1/messages?scope=PROJECT&limit=100", token: TOKENS[:nora])
  expect(code, 200, nora_project, "Nora project view")
  raise "Nora project view lacks own project-internal message" unless contains?(nora_project, "message_id", nora_message_id)
  raise "Need-to-know scope leaked to Nora" if contains?(nora_project, "message_id", message_1)

  code, denied = request(client, :get, "/bus/v1/messages?scope=PROJECT&limit=100", token: TOKENS[:gerd])
  expect_detail(code, 403, denied, "BUS_PROJECT_READ_DENIED", "Participant project read")

  code, denied = request(
    client, :post, "/bus/v1/messages",
    token: TOKENS[:karl],
    request_id: "#{REQUEST_PREFIX}-NEG-PROJECT",
    idempotency_key: "#{IDEMPOTENCY_PREFIX}-NEG-PROJECT",
    body: karl_message.merge(project_id: "OTHER-PROJECT")
  )
  expect_detail(code, 400, denied, "BUS_REQUEST_INVALID", "Outside-project input")

  code, denied = request(
    client, :post, "/bus/v1/messages",
    token: TOKENS[:karl],
    request_id: "#{REQUEST_PREFIX}-NEG-EXTERNAL",
    idempotency_key: "#{IDEMPOTENCY_PREFIX}-NEG-EXTERNAL",
    body: karl_message.merge(action_class: "EXTERNAL_EMAIL")
  )
  expect_detail(code, 400, denied, "BUS_REQUEST_INVALID", "External action")

  code, denied = request(
    client, :post, "/bus/v1/messages/#{nora_message_id}/ack",
    token: TOKENS[:karl],
    request_id: "#{REQUEST_PREFIX}-NEG-ACK",
    body: { decision: "ACCEPTED", note: "Unzulaessige Fremdbestaetigung" }
  )
  expect_detail(code, 403, denied, "BUS_ACK_DENIED", "Non-recipient acknowledgement")

  code, denied = request(
    client, :post, "/bus/v1/messages",
    token: TOKENS[:karl],
    request_id: "#{REQUEST_PREFIX}-NEG-IDEMPOTENCY",
    idempotency_key: "#{IDEMPOTENCY_PREFIX}-KARL-GERD-1",
    body: karl_message.merge(body: "Unzulaessig veraenderter Inhalt")
  )
  expect_detail(code, 409, denied, "BUS_IDEMPOTENCY_CONFLICT", "Idempotency conflict")

  parent = reply_1
  loop_steps = [
    [:karl, "AI-ENG-001", 2],
    [:gerd, "SAO-001", 3],
    [:karl, "AI-ENG-001", 4]
  ]
  loop_steps.each do |actor, recipient, hop|
    code, loop_message = request(
      client, :post, "/bus/v1/messages",
      token: TOKENS.fetch(actor),
      request_id: "#{REQUEST_PREFIX}-LOOP-#{hop}",
      idempotency_key: "#{IDEMPOTENCY_PREFIX}-LOOP-#{hop}",
      body: {
        recipient_id: recipient,
        subject: "API-E2E Schleifenschutz #{hop}",
        body: "Kontrollierter Hop #{hop}",
        action_class: "INTERNAL_STATUS",
        confidentiality: "NEED_TO_KNOW",
        task_ref: TASK_ID,
        handoff_ref: HANDOFF_ID,
        parent_message_id: parent
      }
    )
    expect(code, 201, loop_message, "Loop hop #{hop}")
    raise "Loop hop mismatch" unless loop_message["hop_count"] == hop
    parent = loop_message.fetch("message_id")
  end

  code, denied = request(
    client, :post, "/bus/v1/messages",
    token: TOKENS[:gerd],
    request_id: "#{REQUEST_PREFIX}-LOOP-5",
    idempotency_key: "#{IDEMPOTENCY_PREFIX}-LOOP-5",
    body: {
      recipient_id: "SAO-001",
      subject: "API-E2E Schleifenschutz 5",
      body: "Dieser Hop muss abgewiesen werden.",
      action_class: "INTERNAL_STATUS",
      confidentiality: "NEED_TO_KNOW",
      task_ref: TASK_ID,
      handoff_ref: HANDOFF_ID,
      parent_message_id: parent
    }
  )
  expect_detail(code, 422, denied, "BUS_LOOP_LIMIT_EXCEEDED", "Loop limit")

  code, task = request(
    client, :post, "/bus/v1/tasks/#{TASK_ID}/transition",
    token: TOKENS[:karl],
    request_id: "#{REQUEST_PREFIX}-TASK-DONE",
    body: { new_status: "DONE", completion_evidence: "Realer HTTPS-API-E2E-Lauf technisch bestanden." }
  )
  expect(code, 200, task, "Task completion")
  raise "Task completion mismatch" unless task["task_status"] == "DONE" && task["completed_at"]

  # G-040: the schema no longer answers without a credential. Both halves are
  # checked - that it refuses anonymously, and that the contract check still
  # works for an authorised caller. Closing the finding by deleting this check
  # would have been the worse trade.
  code, _refused = request(client, :get, "/openapi.json")
  expect(code, 401, _refused, "OpenAPI without a key")

  api_key = ENV["WORKFORCE_API_KEY"]
  raise "WORKFORCE_API_KEY is required to inspect the schema" if api_key.nil? || api_key.empty?

  code, openapi = request(client, :get, "/openapi.json", api_key: api_key)
  expect(code, 200, openapi, "OpenAPI inspection")
  paths = openapi.fetch("paths").keys
  forbidden_paths = %w[/bus/v1/admin /bus/v1/credentials /bus/v1/email /bus/v1/whatsapp]
  raise "Forbidden privileged endpoint exposed" unless (paths & forbidden_paths).empty?

  summary = {
    result: "PASS",
    transport: "HTTPS_VERIFIED",
    message_flow: "KARL_GERD_NORA_BIDIRECTIONAL",
    task_status: task["task_status"],
    handoff_status: handoff["handoff_status"],
    idempotency: "PASS",
    project_and_need_to_know_scope: "PASS",
    external_and_privileged_action_denial: "PASS",
    non_recipient_ack_denial: "PASS",
    loop_limit: "PASS",
    forbidden_admin_endpoints: "ABSENT",
    message_ids: [message_1, reply_1, nora_message_id],
    task_id: TASK_ID,
    handoff_id: HANDOFF_ID
  }
end

puts JSON.generate(summary)
