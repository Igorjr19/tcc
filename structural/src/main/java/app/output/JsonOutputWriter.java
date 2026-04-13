package app.output;

import app.model.AnalysisResult;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

/**
 * Serializa o resultado da análise para JSON.
 */
public class JsonOutputWriter {

    private static final Gson GSON = new GsonBuilder()
            .setPrettyPrinting()
            .disableHtmlEscaping()
            .create();

    /**
     * Converte o resultado da análise para uma string JSON formatada.
     */
    public static String toJson(AnalysisResult result) {
        return GSON.toJson(result);
    }
}
