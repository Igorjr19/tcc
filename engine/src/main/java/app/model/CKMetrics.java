package app.model;

/**
 * Métricas CK (Chidamber & Kemerer) calculadas para uma classe.
 */
public class CKMetrics {
    private int cbo;
    private double lcom;
    private int dit;
    private int noc;
    private int rfc;
    private int numberOfMethods;
    private int numberOfAttributes;
    private int linesOfCode;

    public int getCbo() { return cbo; }
    public void setCbo(int cbo) { this.cbo = cbo; }

    public double getLcom() { return lcom; }
    public void setLcom(double lcom) { this.lcom = lcom; }

    public int getDit() { return dit; }
    public void setDit(int dit) { this.dit = dit; }

    public int getNoc() { return noc; }
    public void setNoc(int noc) { this.noc = noc; }

    public int getRfc() { return rfc; }
    public void setRfc(int rfc) { this.rfc = rfc; }

    public int getNumberOfMethods() { return numberOfMethods; }
    public void setNumberOfMethods(int numberOfMethods) { this.numberOfMethods = numberOfMethods; }

    public int getNumberOfAttributes() { return numberOfAttributes; }
    public void setNumberOfAttributes(int numberOfAttributes) { this.numberOfAttributes = numberOfAttributes; }

    public int getLinesOfCode() { return linesOfCode; }
    public void setLinesOfCode(int linesOfCode) { this.linesOfCode = linesOfCode; }
}
