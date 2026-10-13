import groovy.json.JsonOutput

/** Successful task receipts survive Nextflow cache reuse. Never capture the environment. */
class DapReceipt {
    static String command(task, String step, List subjects, engine, boolean stub = false) {
        def name = "${step}.${subjects[0]}.genesis-task.json"
        def data = [schema_version: 1, step: step, subjects: subjects,
                    mode: stub ? 'stub' : 'real', attempt: task.attempt,
                    engine: engine ?: 'none', container: task.container?.toString(),
                    requested: [cpus: task.cpus, memory_bytes: task.memory.toBytes(),
                                time_ms: task.time.toMillis()],
                    observed: null]
        def json = JsonOutput.toJson(data)
        // The script hash binds site-config overrides as well as the checked-in module.
        return """cat > '${name}' << 'GENESIS_TASK_RECEIPT'
${json.substring(0, json.length() - 1)},"script_sha256":
GENESIS_TASK_RECEIPT
printf '\"%s\"}\\n' "\$(sha256sum .command.sh | cut -d ' ' -f 1)" >> '${name}'
"""
    }
}
