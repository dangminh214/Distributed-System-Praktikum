FROM maven:3.8.1-openjdk-17-slim as builder
WORKDIR /app
COPY pom.xml /app
COPY src/main/java/connection /app/src/main/java/connection
COPY src/main/java/borse /app/src/main/java/borse
RUN sed -i 's/to substitute/borse.Main/' pom.xml
RUN mvn assembly:assembly -DdescriptorId=jar-with-dependencies

FROM openjdk:18-slim
WORKDIR /app
COPY --from=builder app/target/app-1.0-jar-with-dependencies.jar /app/app.jar
