FROM maven:3.8.1-openjdk-17-slim as builder
WORKDIR /app
COPY pom.xml /app
COPY src /app/src
RUN sed -i 's/to substitute/bank.Main/' pom.xml
RUN mvn assembly:assembly -DdescriptorId=jar-with-dependencies

# Run stage
FROM openjdk:18-slim
WORKDIR /app
COPY --from=builder app/target/app-1.0-jar-with-dependencies.jar /app/app.jar
