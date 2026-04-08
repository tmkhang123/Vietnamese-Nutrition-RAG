package com.webdinhduong.chatbot.controller;

import com.webdinhduong.chatbot.entity.FoodRecord;
import com.webdinhduong.chatbot.entity.User;
import com.webdinhduong.chatbot.repository.FoodRecordRepository;
import com.webdinhduong.chatbot.repository.UserRepository;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;

@RestController
@RequestMapping("/api/chat")
@CrossOrigin(origins = "*")
public class ChatController {
    private static final Logger log = LoggerFactory.getLogger(ChatController.class);

    @Autowired
    private FoodRecordRepository foodRecordRepository;

    @Autowired
    private UserRepository userRepository;

    private final ObjectMapper objectMapper = new ObjectMapper();

    // Can be absolute path, or relative to current working directory.
    @Value("${rag.cliScript:HeThongDeXuatThucAn/main/rag_cli.py}")
    private String ragCliScript;

    @Value("${rag.timeoutMs:120000}")
    private long ragTimeoutMs;

    @Value("${rag.pythonExecutable:python}")
    private String ragPythonExecutable;

    // API nhận tin nhắn từ người dùng
    @PostMapping("/send")
    public ResponseEntity<?> sendMessage(@RequestParam Long userId, @RequestBody Map<String, String> payload) {
        String userMessage = payload.get("message");

        // --- BƯỚC 1: GỌI MODEL AI (Python) ĐỂ LẤY CÂU TRẢ LỜI + THÔNG TIN CHO DASHBOARD ---
        String aiResponse = null;
        String savedFoodName = null;
        String savedCalories = null;

        try {
            Map<String, Object> ragResult = callRagModel(userMessage);

            aiResponse = (String) ragResult.getOrDefault("answer", null);

            @SuppressWarnings("unchecked")
            Map<String, Object> entities = (Map<String, Object>) ragResult.get("entities");
            if (entities != null) {
                @SuppressWarnings("unchecked")
                List<String> foods = (List<String>) entities.get("foods");
                if (foods != null && !foods.isEmpty()) {
                    savedFoodName = foods.get(0);
                }
            }

            @SuppressWarnings("unchecked")
            Map<String, Object> energy = (Map<String, Object>) ragResult.get("energy");
            if (energy != null) {
                Object amount = energy.get("amountPer100g");
                Object unit = energy.get("unitName");
                if (amount != null && unit != null) {
                    savedCalories = amount + " " + unit + " / 100g";
                }
            }
        } catch (Exception e) {
            log.error("Không gọi được RAG model", e);
            // Fallback để không làm hỏng luồng chat khi Python/Ollama chưa sẵn sàng.
            aiResponse = "Hệ thống AI: Hiện tại chưa gọi được mô hình. Vui lòng thử lại sau nhé.";
        }

        if (aiResponse == null) {
            aiResponse = "Xin lỗi, tôi chưa hiểu ý bạn.";
        }

        if (savedFoodName != null) {
            User user = userRepository.findById(userId).orElseThrow();
            FoodRecord record = new FoodRecord();
            record.setUser(user);
            record.setFoodName(savedFoodName);
            record.setCalories(savedCalories != null ? savedCalories : "Đang cập nhật từ AI...");
            foodRecordRepository.save(record);
        }

        return ResponseEntity.ok(Map.of("response", aiResponse));
    }

    // API Lấy danh sách món ăn cho Dashboard
    @GetMapping("/dashboard/{userId}")
    public ResponseEntity<List<FoodRecord>> getDashboard(@PathVariable Long userId) {
        return ResponseEntity.ok(foodRecordRepository.findByUserIdOrderByCreatedAtDesc(userId));
    }

    private Map<String, Object> callRagModel(String userMessage) throws IOException, InterruptedException {
        Path scriptPath = resolveRagScriptPath();

        ProcessBuilder pb = new ProcessBuilder(
                ragPythonExecutable,
                scriptPath.toString(),
                userMessage
        );
        pb.redirectErrorStream(true);
        pb.environment().put("PYTHONIOENCODING", "utf-8");

        pb.directory(scriptPath.getParent().toFile());

        Process process = pb.start();
        boolean finished = process.waitFor(ragTimeoutMs, TimeUnit.MILLISECONDS);
        if (!finished) {
            process.destroyForcibly();
            throw new IOException("Gọi mô hình AI bị timeout.");
        }

        int exitCode = process.exitValue();
        String output = new String(process.getInputStream().readAllBytes(), StandardCharsets.UTF_8).trim();
        if (output.isEmpty()) {
            throw new IOException("Mô hình AI trả về dữ liệu rỗng.");
        }
        if (exitCode != 0) {
            throw new IOException("RAG CLI thất bại (exit=" + exitCode + "): " + output);
        }

        return objectMapper.readValue(output, new TypeReference<Map<String, Object>>() {});
    }

    private Path resolveRagScriptPath() throws IOException {
        Path configured = Paths.get(ragCliScript);
        if (configured.isAbsolute() && Files.exists(configured)) {
            return configured.normalize();
        }

        Path cwd = Paths.get(System.getProperty("user.dir"));
        List<Path> candidates = new ArrayList<>();
        candidates.add(cwd.resolve(ragCliScript).normalize());
        candidates.add(cwd.resolve("HeThongDeXuatThucAn/main/rag_cli.py").normalize());
        candidates.add(cwd.resolve("main/rag_cli.py").normalize());
        candidates.add(cwd.resolve("Interface/chatbot/../../main/rag_cli.py").normalize());
        candidates.add(cwd.resolve("HeThongDeXuatThucAn/Interface/chatbot/../../main/rag_cli.py").normalize());

        for (Path candidate : candidates) {
            if (Files.exists(candidate)) {
                return candidate;
            }
        }

        throw new IOException("Không tìm thấy rag_cli.py. Đã thử: " + candidates);
    }
}